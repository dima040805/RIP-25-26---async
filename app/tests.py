from unittest import mock

from django.test import SimpleTestCase
from rest_framework.test import APIClient

from app import views


class HealthCheckTests(SimpleTestCase):
    def test_health(self):
        response = APIClient().get("/api/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")


class CalculateRadiusEndpointTests(SimpleTestCase):
    def test_missing_fields_are_rejected(self):
        response = APIClient().post(
            "/api/calculate-radius/", {"research_id": 1}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    @mock.patch.object(views, "executor")
    def test_calculation_is_submitted(self, executor):
        payload = {
            "research_id": 1,
            "planet_id": 2,
            "star_radius": 100000,
            "planet_shine": 1.0,
        }
        response = APIClient().post("/api/calculate-radius/", payload, format="json")

        self.assertEqual(response.status_code, 202)
        executor.submit.assert_called_once_with(
            views.calculate_planet_radius_single, 1, 2, 100000, 1.0
        )
        executor.submit.return_value.add_done_callback.assert_called_once_with(
            views.send_calculation_result
        )


class CalculationTests(SimpleTestCase):
    @mock.patch.object(views.time, "sleep")
    def test_radius_formula(self, _sleep):
        result = views.calculate_planet_radius_single(1, 2, 100000, 1.0)
        self.assertTrue(result["success"])
        self.assertEqual(result["radius_km"], 10000)

    @mock.patch.object(views.time, "sleep")
    def test_non_positive_shine_fails(self, _sleep):
        result = views.calculate_planet_radius_single(1, 2, 100000, 0)
        self.assertFalse(result["success"])

    @mock.patch.object(views.requests, "put")
    def test_successful_result_is_sent_back(self, put):
        task = mock.Mock()
        task.result.return_value = {
            "research_id": 1,
            "planet_id": 2,
            "radius_km": 10000,
            "success": True,
        }
        views.send_calculation_result(task)

        url = put.call_args.args[0]
        self.assertTrue(url.endswith("/research/1/radius"))
        self.assertEqual(put.call_args.kwargs["json"]["planet_radius"], 10000)
        self.assertEqual(put.call_args.kwargs["headers"]["Authorization"], views.AUTH_TOKEN)

    @mock.patch.object(views.requests, "put")
    def test_failed_result_is_not_sent(self, put):
        task = mock.Mock()
        task.result.return_value = {
            "research_id": 1,
            "planet_id": 2,
            "radius_km": 0,
            "success": False,
        }
        views.send_calculation_result(task)
        put.assert_not_called()
