"""Minimal model client. `complete` returns the model's JSON, parsed and
trusted as-is — the caller decides what to do with it."""

import json
import os
from openai import OpenAI

_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


class _Model:
    def complete(self, prompt):
        resp = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        return json.loads(resp.choices[0].message.content)


model = _Model()
