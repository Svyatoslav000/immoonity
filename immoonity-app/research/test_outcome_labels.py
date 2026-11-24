import unittest

from outcome_labels import Event, status_by_day


class TestOutcomes(unittest.TestCase):
    def label(self, day, events=(), negative=12, end=41, eligible=True):
        return status_by_day(day, last_joint_negative=negative, followup_end=end,
                             events=list(events), event_free_at_launch=eligible)

    def test_between_tests(self):
        events = [Event("immune_deficiency_with_disease", 26, 12)]
        for day, want in [(12, "observed_event_free"), (13, "unknown"), (25, "unknown"),
                          (26, "observed_event"), (80, "observed_event")]:
            self.assertEqual(self.label(day, events), want)

    def test_union_counts_first_event(self):
        both = [Event("mission_failure", 35), Event("immune_deficiency_with_disease", 18)]
        self.assertEqual(self.label(18, both), "observed_event")
        self.assertEqual(self.label(15, both), "unknown")

    def test_missing_and_censored(self):
        self.assertEqual(self.label(35, negative=None), "unknown")
        self.assertEqual(self.label(45), "followup_ended")
        self.assertEqual(self.label(1, eligible=None), "baseline_ineligible_or_unknown")
        self.assertEqual(self.label(1, eligible=False), "baseline_ineligible_or_unknown")

    def test_independent_adjudication(self):
        with self.assertRaises(ValueError):
            self.label(15, [Event("positive_saliva_pcr", 14)])
        with self.assertRaises(ValueError):
            self.label(20, [Event("mission_failure", 10)])
        with self.assertRaises(ValueError):
            self.label(20, [Event("mission_failure", 22, 25)])


if __name__ == "__main__":
    unittest.main()
