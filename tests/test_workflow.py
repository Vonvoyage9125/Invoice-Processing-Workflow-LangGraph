import unittest
import json
import os
import tempfile
import shutil
from src.runner import run_workflow
from src import db
from src.nodes import *
from src.bigtool import BigtoolPicker


class TestWorkflowIntegration(unittest.TestCase):
    """Integration tests for the full invoice workflow."""

    def setUp(self):
        """Create a temporary DB for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')

    def tearDown(self):
        """Clean up temp DB."""
        import sqlite3
        # Close any open connections to prevent file locks on Windows
        try:
            sqlite3.connect(self.db_path).close()
        except Exception:
            pass
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception:
            pass

    def _sample_invoice(self):
        return {
            'invoice_id': 'TEST-001',
            'vendor_name': 'Test Vendor',
            'vendor_tax_id': 'TAX123',
            'invoice_date': '2025-01-01',
            'due_date': '2025-02-01',
            'amount': 5000.0,
            'currency': 'USD',
            'line_items': [
                {'desc': 'Item 1', 'qty': 1, 'unit_price': 5000.0, 'total': 5000.0}
            ],
            'attachments': ['invoice.pdf']
        }

    def test_workflow_happy_path_auto_accept(self):
        """Test workflow runs to completion with auto ACCEPT decision."""
        inv = self._sample_invoice()
        state = run_workflow(inv, self.db_path, auto_decide=True, decision_delay=0)
        
        # Verify final payload exists
        self.assertIn('final_payload', state)
        self.assertEqual(state['final_payload']['status'], 'COMPLETED')
        self.assertEqual(state['invoice']['invoice_id'], 'TEST-001')

    def test_workflow_manual_accept(self):
        """Test workflow pauses and resumes on manual ACCEPT."""
        inv = self._sample_invoice()
        conn = db.init_db(self.db_path)
        state = {'invoice': inv}
        config = {'match_threshold': 0.9}
        
        # Run through stages
        nodes = [
            IngestNode(conn, config),
            OcrNlpNode(conn, config),
            NormalizeEnrichNode(conn, config),
            ErpFetchNode(conn, config),
            TwoWayMatcherNode(conn, config),
            CheckpointNode(conn, config),
        ]
        
        for node in nodes:
            state = node.run(state)
        
        # Should have paused with checkpoint
        self.assertTrue(state.get('paused'))
        checkpoint_id = state.get('checkpoint_id')
        self.assertIsNotNone(checkpoint_id)
        
        # Simulate manual decision
        db.save_decision(conn, checkpoint_id, 'tester', 'ACCEPT')
        
        # Verify decision persisted
        pending = db.fetch_checkpoint(conn, checkpoint_id)
        self.assertEqual(pending['status'], 'DECIDED')

    def test_checkpoint_persistence(self):
        """Test checkpoint state is persisted to DB."""
        inv = self._sample_invoice()
        conn = db.init_db(self.db_path)
        checkpoint_id = 'TEST-CHECKPOINT-001'
        state = {
            'invoice': inv,
            'raw_id': 'raw-123',
            'parsed_invoice': {'invoice_text': 'test'},
            'vendor_profile': {'normalized_name': 'Test'}
        }
        
        # Save checkpoint
        db.save_checkpoint(conn, checkpoint_id, inv['invoice_id'], state)
        
        # Fetch and verify
        fetched = db.fetch_checkpoint(conn, checkpoint_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched['id'], checkpoint_id)
        self.assertEqual(fetched['invoice_id'], inv['invoice_id'])
        self.assertIn('parsed_invoice', fetched['state'])

    def test_audit_log(self):
        """Test audit entries are recorded."""
        inv = self._sample_invoice()
        conn = db.init_db(self.db_path)
        
        # Append audit entries
        db.append_audit(conn, inv['invoice_id'], 'INTAKE', 'Test message 1')
        db.append_audit(conn, inv['invoice_id'], 'UNDERSTAND', 'Test message 2')
        
        # Query audit (manual SQL for now)
        cur = conn.cursor()
        cur.execute("SELECT stage, message FROM audit_log WHERE invoice_id=?", (inv['invoice_id'],))
        rows = cur.fetchall()
        
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0], 'INTAKE')
        self.assertEqual(rows[1][0], 'UNDERSTAND')

    def test_bigtool_picker(self):
        """Test Bigtool pool selection."""
        picker = BigtoolPicker()
        
        ocr_pick = picker.select('ocr')
        self.assertIn(ocr_pick, ['google_vision', 'tesseract', 'aws_textract'])
        
        enrichment_pick = picker.select('enrichment')
        self.assertIn(enrichment_pick, ['clearbit', 'people_data_labs', 'vendor_db'])
        
        erp_pick = picker.select('erp_connector')
        self.assertIn(erp_pick, ['sap_sandbox', 'netsuite', 'mock_erp'])

    def test_node_state_propagation(self):
        """Test that state is correctly passed through nodes."""
        inv = self._sample_invoice()
        conn = db.init_db(self.db_path)
        config = {'match_threshold': 0.9}
        state = {'invoice': inv}
        
        # Run INTAKE
        node = IngestNode(conn, config)
        state = node.run(state)
        self.assertIn('raw_id', state['invoice'])
        self.assertIsNotNone(state['invoice']['raw_id'])
        
        # Run UNDERSTAND
        node = OcrNlpNode(conn, config)
        state = node.run(state)
        self.assertIn('parsed_invoice', state)
        self.assertIn('parsed_line_items', state['parsed_invoice'])


class TestBigtoolPicker(unittest.TestCase):
    """Unit tests for Bigtool picker."""

    def test_picker_fallback_on_missing_pool(self):
        """Test Bigtool falls back gracefully when pool is missing."""
        picker = BigtoolPicker(pools={})
        result = picker.select('unknown_capability')
        self.assertEqual(result, 'mock_tool')

    def test_picker_custom_pools(self):
        """Test Bigtool with custom pools."""
        custom_pools = {
            'ocr': ['custom_ocr_tool']
        }
        picker = BigtoolPicker(pools=custom_pools)
        result = picker.select('ocr')
        self.assertEqual(result, 'custom_ocr_tool')


class TestCheckpointAndResume(unittest.TestCase):
    """Test HITL checkpoint creation and resume logic."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_checkpoint_creation_on_match_failure(self):
        """Test checkpoint is created when match fails."""
        inv = {
            'invoice_id': 'FAIL-001',
            'vendor_name': 'Vendor',
            'amount': 10000.0,
            'currency': 'USD',
            'line_items': [],
            'attachments': []
        }
        conn = db.init_db(self.db_path)
        config = {'match_threshold': 0.9}
        state = {
            'invoice': inv,
            'matched_pos': []  # Empty POs to force low match score
        }
        
        # Run matcher
        node = TwoWayMatcherNode(conn, config)
        state = node.run(state)
        self.assertEqual(state['match_result'], 'FAILED')
        
        # Now run checkpoint node
        node = CheckpointNode(conn, config)
        state = node.run(state)
        self.assertTrue(state.get('paused'))
        self.assertIsNotNone(state.get('checkpoint_id'))

    def test_list_pending_checkpoints(self):
        """Test fetching pending checkpoints."""
        conn = db.init_db(self.db_path)
        
        # Create 2 checkpoints
        state1 = {'invoice': {'invoice_id': 'INV1', 'amount': 100}}
        state2 = {'invoice': {'invoice_id': 'INV2', 'amount': 200}}
        
        db.save_checkpoint(conn, 'CP1', 'INV1', state1)
        db.save_checkpoint(conn, 'CP2', 'INV2', state2)
        
        pending = db.list_pending(conn)
        self.assertEqual(len(pending), 2)
        self.assertEqual(pending[0]['checkpoint_id'], 'CP1')
        self.assertEqual(pending[1]['checkpoint_id'], 'CP2')


if __name__ == '__main__':
    unittest.main()
