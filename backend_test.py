#!/usr/bin/env python3
"""
Comprehensive backend API test suite for WebForge pipeline.
Tests all endpoints and runs a full E2E pipeline on example.com.
"""
import requests
import sys
import time
import io
from datetime import datetime

# Public backend URL from frontend/.env
BASE_URL = "https://web-upgrade-engine.preview.emergentagent.com/api"

class WebForgeAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.tests_run = 0
        self.tests_passed = 0
        self.test_job_id = None
        self.e2e_job_id = None

    def log(self, emoji, message):
        """Print formatted log message"""
        print(f"{emoji} {message}")

    def test(self, name, func):
        """Run a single test"""
        self.tests_run += 1
        self.log("🔍", f"Testing: {name}")
        try:
            func()
            self.tests_passed += 1
            self.log("✅", f"PASSED: {name}")
            return True
        except AssertionError as e:
            self.log("❌", f"FAILED: {name} - {e}")
            return False
        except Exception as e:
            self.log("❌", f"ERROR: {name} - {e}")
            return False

    def test_health_check(self):
        """Test GET /api/ returns ok=true, has_vercel_token=true, has_llm_key=true"""
        resp = requests.get(f"{self.base_url}/")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert data.get("ok") is True, f"Expected ok=true, got {data.get('ok')}"
        assert data.get("has_vercel_token") is True, f"Expected has_vercel_token=true, got {data.get('has_vercel_token')}"
        assert data.get("has_llm_key") is True, f"Expected has_llm_key=true, got {data.get('has_llm_key')}"
        self.log("📊", f"Health check: {data}")

    def test_create_job(self):
        """Test POST /api/jobs creates a job with 6 stages"""
        payload = {"input_url": "https://example.com"}
        resp = requests.post(f"{self.base_url}/jobs", json=payload)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "id" in data, "Job should have an id"
        assert data.get("input_url") == "https://example.com", f"Expected input_url=https://example.com, got {data.get('input_url')}"
        assert data.get("status") == "queued", f"Expected status=queued, got {data.get('status')}"
        assert len(data.get("steps", [])) == 6, f"Expected 6 steps, got {len(data.get('steps', []))}"
        
        # Verify step keys
        expected_keys = ["scrape", "analyze", "reference", "generate", "qa", "deploy"]
        actual_keys = [s["key"] for s in data.get("steps", [])]
        assert actual_keys == expected_keys, f"Expected steps {expected_keys}, got {actual_keys}"
        
        self.test_job_id = data["id"]
        self.log("📝", f"Created job: {self.test_job_id}")

    def test_list_jobs(self):
        """Test GET /api/jobs returns list sorted desc"""
        resp = requests.get(f"{self.base_url}/jobs")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        if len(data) > 1:
            # Check descending order by created_at
            for i in range(len(data) - 1):
                assert data[i]["created_at"] >= data[i+1]["created_at"], "Jobs should be sorted desc by created_at"
        self.log("📋", f"Found {len(data)} jobs")

    def test_get_job(self):
        """Test GET /api/jobs/{id} returns full job"""
        if not self.test_job_id:
            raise AssertionError("No test_job_id available")
        resp = requests.get(f"{self.base_url}/jobs/{self.test_job_id}")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert data["id"] == self.test_job_id, f"Expected id={self.test_job_id}, got {data['id']}"
        assert "qa_original" in data, "Job should have qa_original"
        assert "qa_generated" in data, "Job should have qa_generated"
        assert "pages_plan" in data, "Job should have pages_plan"
        assert "design_tokens" in data, "Job should have design_tokens"
        self.log("🔎", f"Job detail retrieved: {data['id']}")

    def test_get_logs(self):
        """Test GET /api/jobs/{id}/logs returns logs array"""
        if not self.test_job_id:
            raise AssertionError("No test_job_id available")
        resp = requests.get(f"{self.base_url}/jobs/{self.test_job_id}/logs")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        self.log("📜", f"Retrieved {len(data)} logs")

    def test_video_upload_rejection(self):
        """Test POST /api/jobs/{id}/upload-video rejects invalid extensions"""
        if not self.test_job_id:
            raise AssertionError("No test_job_id available")
        
        # Create a fake .txt file
        fake_file = io.BytesIO(b"fake video content")
        files = {"file": ("test.txt", fake_file, "text/plain")}
        resp = requests.post(f"{self.base_url}/jobs/{self.test_job_id}/upload-video", files=files)
        assert resp.status_code == 400, f"Expected 400 for invalid extension, got {resp.status_code}"
        self.log("🚫", "Video upload correctly rejected .txt file")

    def test_delete_job(self):
        """Test DELETE /api/jobs/{id} removes job"""
        if not self.test_job_id:
            raise AssertionError("No test_job_id available")
        resp = requests.delete(f"{self.base_url}/jobs/{self.test_job_id}")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert data.get("ok") is True, f"Expected ok=true, got {data.get('ok')}"
        
        # Verify job is deleted
        resp2 = requests.get(f"{self.base_url}/jobs/{self.test_job_id}")
        assert resp2.status_code == 404, f"Expected 404 after deletion, got {resp2.status_code}"
        self.log("🗑️", f"Job deleted: {self.test_job_id}")

    def test_e2e_pipeline(self):
        """
        CRITICAL E2E TEST: Run full pipeline on example.com
        - Wait up to 4 minutes for completion
        - Verify status='deployed'
        - Verify deploy_url is publicly accessible (HTTP 200 without auth)
        - Verify pipeline steps progress correctly
        - Verify QA scores structure
        - Verify pages_plan and design_tokens
        """
        self.log("🚀", "Starting E2E pipeline test on https://example.com (up to 4 minutes)")
        
        # Create job
        payload = {"input_url": "https://example.com"}
        resp = requests.post(f"{self.base_url}/jobs", json=payload)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        job = resp.json()
        self.e2e_job_id = job["id"]
        self.log("📝", f"E2E job created: {self.e2e_job_id}")
        
        # Poll job status for up to 4 minutes (240 seconds)
        start_time = time.time()
        timeout = 240
        last_status = None
        last_step_statuses = {}
        
        while time.time() - start_time < timeout:
            resp = requests.get(f"{self.base_url}/jobs/{self.e2e_job_id}")
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
            job = resp.json()
            
            current_status = job.get("status")
            if current_status != last_status:
                self.log("📊", f"Job status: {current_status}")
                last_status = current_status
            
            # Log step progress
            for step in job.get("steps", []):
                key = step["key"]
                status = step["status"]
                if last_step_statuses.get(key) != status:
                    self.log("🔄", f"  Step {key}: {status}")
                    last_step_statuses[key] = status
            
            # Check if pipeline completed
            if current_status in ["deployed", "failed"]:
                break
            
            time.sleep(5)  # Poll every 5 seconds
        
        # Verify final status
        assert job.get("status") == "deployed", f"Expected status=deployed, got {job.get('status')}. Error: {job.get('error')}"
        self.log("✅", f"Pipeline completed with status: {job['status']}")
        
        # Verify all steps are done
        expected_order = ["scrape", "analyze", "reference", "generate", "qa", "deploy"]
        for step_key in expected_order:
            step = next((s for s in job["steps"] if s["key"] == step_key), None)
            assert step is not None, f"Step {step_key} not found"
            assert step["status"] == "done", f"Step {step_key} should be done, got {step['status']}"
        self.log("✅", "All pipeline steps completed in correct order")
        
        # Verify QA scores structure
        qa_orig = job.get("qa_original", {})
        qa_gen = job.get("qa_generated", {})
        
        for qa_name, qa_data in [("qa_original", qa_orig), ("qa_generated", qa_gen)]:
            assert "anti_slop" in qa_data, f"{qa_name} should have anti_slop score"
            assert "palette" in qa_data, f"{qa_name} should have palette score"
            assert "mobile" in qa_data, f"{qa_name} should have mobile score"
            assert "overall" in qa_data, f"{qa_name} should have overall score"
            
            # Verify scores are numeric 0-100
            for score_key in ["anti_slop", "palette", "mobile", "overall"]:
                score = qa_data[score_key]
                assert isinstance(score, (int, float)), f"{qa_name}.{score_key} should be numeric, got {type(score)}"
                assert 0 <= score <= 100, f"{qa_name}.{score_key} should be 0-100, got {score}"
        
        self.log("✅", f"QA scores valid - Original: {qa_orig['overall']}/100, Generated: {qa_gen['overall']}/100")
        
        # Verify pages_plan has at least 3 pages
        pages_plan = job.get("pages_plan", [])
        assert len(pages_plan) >= 3, f"Expected at least 3 pages, got {len(pages_plan)}"
        self.log("✅", f"Pages plan has {len(pages_plan)} pages")
        
        # Verify design_tokens has colors
        design_tokens = job.get("design_tokens", {})
        assert "primary" in design_tokens or "bg" in design_tokens or "fg" in design_tokens, \
            f"design_tokens should have color keys, got {list(design_tokens.keys())}"
        self.log("✅", f"Design tokens present: {list(design_tokens.keys())}")
        
        # Verify deploy_url exists and is publicly accessible
        deploy_url = job.get("deploy_url")
        assert deploy_url, "deploy_url should not be empty"
        assert deploy_url.startswith("http"), f"deploy_url should be a valid URL, got {deploy_url}"
        
        self.log("🌐", f"Testing public accessibility of: {deploy_url}")
        
        # Test public access (no auth headers)
        try:
            resp = requests.get(deploy_url, timeout=30, allow_redirects=True)
            assert resp.status_code == 200, f"Expected 200 from deploy_url, got {resp.status_code}"
            self.log("✅", f"Deploy URL is publicly accessible: {deploy_url}")
        except Exception as e:
            raise AssertionError(f"Deploy URL not accessible: {e}")
        
        self.log("🎉", f"E2E pipeline test PASSED! Deploy URL: {deploy_url}")

    def run_all_tests(self):
        """Run all tests in sequence"""
        self.log("🚀", "Starting WebForge API Test Suite")
        self.log("🔗", f"Backend URL: {self.base_url}")
        print("=" * 80)
        
        # Basic API tests
        self.test("Health Check", self.test_health_check)
        self.test("Create Job", self.test_create_job)
        self.test("List Jobs", self.test_list_jobs)
        self.test("Get Job Detail", self.test_get_job)
        self.test("Get Job Logs", self.test_get_logs)
        self.test("Video Upload Rejection", self.test_video_upload_rejection)
        self.test("Delete Job", self.test_delete_job)
        
        # E2E pipeline test (most critical)
        self.test("E2E Pipeline (example.com)", self.test_e2e_pipeline)
        
        # Print summary
        print("=" * 80)
        self.log("📊", f"Tests completed: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            self.log("🎉", "ALL TESTS PASSED!")
            return 0
        else:
            self.log("⚠️", f"{self.tests_run - self.tests_passed} test(s) failed")
            return 1

def main():
    tester = WebForgeAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())
