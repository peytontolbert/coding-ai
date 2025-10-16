from typing import Any, Dict
import os


class LLMClient:
    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.model_id = self.config.get("model_id") or os.environ.get(
            "HF_MODEL_ID", "meta-llama/Meta-Llama-3-8B-Instruct"
        )
        self.max_new_tokens = int(self.config.get("max_new_tokens", 512))
        self.temperature = float(self.config.get("temperature", 0.2))
        self._pipe = None

    def _ensure_pipeline(self) -> None:
        if self._pipe is not None:
            return
        # Lazy import to keep startup light
        from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline  # type: ignore

        hf_token = os.environ.get("HF_TOKEN") or os.environ.get(
            "HUGGINGFACEHUB_API_TOKEN"
        )
        tok_kwargs = {}
        mdl_kwargs = {"trust_remote_code": True}
        if hf_token:
            # Backwards compatibility across transformers versions
            tok_kwargs["token"] = hf_token
            mdl_kwargs["token"] = hf_token
            tok_kwargs["use_auth_token"] = hf_token
            mdl_kwargs["use_auth_token"] = hf_token
        tokenizer = AutoTokenizer.from_pretrained(self.model_id, **tok_kwargs)
        try:
            import torch  # type: ignore

            torch_dtype = getattr(torch, "bfloat16", None) or getattr(
                torch, "float16", None
            )
            mdl_kwargs["torch_dtype"] = torch_dtype
        except Exception:
            pass
        model = AutoModelForCausalLM.from_pretrained(
            self.model_id, device_map="auto", **mdl_kwargs
        )
        self._pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            do_sample=(self.temperature > 0),
            temperature=self.temperature,
            max_new_tokens=self.max_new_tokens,
            return_full_text=False,
        )

    def generate_diff(self, prompt: str, context: str) -> str:
        self._ensure_pipeline()
        sys_inst = (
            "You are a code refactoring assistant. Emit only unified diffs from repo root. "
            "No explanations. Maintain invariants and keep tests green."
        )
        user_msg = (
            "Objective:\n"
            + prompt.strip()
            + "\n\nContext:\n"
            + context.strip()
            + "\n\nCodeGraph context: Provide surgical edits. Emit a single unified diff."
        )
        # Simple chat template for instruct models
        text_in = f"<|system|>\n{sys_inst}\n<|user|>\n{user_msg}\n<|assistant|>\n"
        out = self._pipe(text_in)[0]["generated_text"]
        return str(out).strip()
