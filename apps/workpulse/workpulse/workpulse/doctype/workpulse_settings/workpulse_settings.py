from frappe.model.document import Document


class WorkPulseSettings(Document):
	@staticmethod
	def get_settings():
		return __import__("frappe").get_single("WorkPulse Settings")

	def validate(self):
		defaults = {
			"daily_hours": 8,
			"meeting_overhead_pct": 10,
			"workload_ceiling_pct": 100,
			"workload_warn_pct": 85,
			"w_skill": 0.4,
			"w_capacity": 0.25,
			"w_history": 0.2,
			"w_reliability": 0.15,
			"default_task_hours": 8,
			"min_samples_for_ml": 300,
			"llm_enabled": 0,
			"llm_provider": "OpenAI-compatible",
			"llm_model": "gpt-4o-mini",
			"llm_api_key_env": "WORKPULSE_LLM_API_KEY",
			"llm_endpoint": "https://api.openai.com/v1/chat/completions",
			"ml_enabled": 0,
			"lookahead_days": 7,
		}
		for fieldname, fallback in defaults.items():
			if getattr(self, fieldname, None) in (None, ""):
				setattr(self, fieldname, fallback)
			elif fieldname in {"w_skill", "w_capacity", "w_history", "w_reliability"}:
				setattr(self, fieldname, float(getattr(self, fieldname)))

		self.enabled = 1 if self.enabled is None else self.enabled