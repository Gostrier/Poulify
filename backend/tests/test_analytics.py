import datetime

import pytest

from core import analytics


class FakeFlock:
    def __init__(self, flock_id, initial_count, name="Test Flock"):
        self.id = flock_id
        self.initial_count = initial_count
        self.name = name


class FakeLog:
    def __init__(self, flock_id, log_date, feed, weight, mortality, water, eggs):
        self.flock_id = flock_id
        self.log_date = log_date
        self.feed_consumed_kg = feed
        self.avg_bird_weight_g = weight
        self.mortality_count = mortality
        self.water_consumed_liters = water
        self.eggs_collected = eggs
        self.flock = FakeFlock(flock_id, 100)


class FakeVaccination:
    def __init__(self, completed, scheduled_date, flock_name="Test Flock"):
        self.is_completed = completed
        self.scheduled_date = scheduled_date
        self.vaccine_name = "Newcastle"
        self.flock = FakeFlock(1, 100, flock_name)


def make_logs():
    return [
        FakeLog(1, datetime.date(2026, 1, 1), 5.0, 100.0, 1, 10.0, 20),
        FakeLog(1, datetime.date(2026, 1, 2), 5.0, 500.0, 2, 10.0, 30),
        FakeLog(1, datetime.date(2026, 1, 3), 5.0, 900.0, 0, 10.0, 40),
    ]


def test_empty_logs_returns_no_data():
    result = analytics.process_poultry_data([])
    assert result["status"] == "No Data"
    assert result["survival_rate"] == 100
    assert result["alerts"] == []


def test_mortality_and_survival():
    result = analytics.process_poultry_data(make_logs())
    assert result["total_mortality"] == 3
    assert result["current_birds"] == 97
    assert result["survival_rate"] == 97.0


def test_financials():
    class FakeExpense:
        def __init__(self, amount):
            self.amount = amount

    class FakeRevenue:
        def __init__(self, amount):
            self.amount = amount

    expenses = [FakeExpense(100), FakeExpense(100)]
    revenues = [FakeRevenue(300)]
    result = analytics.process_poultry_data(make_logs(), expenses, revenues)
    assert result["total_expenses"] == 200
    assert result["total_revenue"] == 300
    assert result["profit"] == 100
    assert result["roi"] == 50.0


def test_vaccination_due_alert():
    overdue = FakeVaccination(completed=False, scheduled_date=datetime.date.today())
    result = analytics.process_poultry_data(make_logs(), vaccinations=[overdue])
    assert any("Vaccination Due" in a for a in result["alerts"])


def test_completed_vaccination_no_alert():
    done = FakeVaccination(completed=True, scheduled_date=datetime.date.today())
    result = analytics.process_poultry_data(make_logs(), vaccinations=[done])
    assert all("Vaccination Due" not in a for a in result["alerts"])
