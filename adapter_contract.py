"""Future extraction provider interface. No credentials or network implementation."""
from typing import Protocol

class ExtractionProvider(Protocol):
    def extract(self, pages: list[str]) -> dict[str, str]:
        """Return invoice/date/subtotal/tax/total/currency/source_page strings.

        Raise ValueError for refusal, ambiguity, unsupported input or invalid schema.
        Callers must validate, display source evidence and require human approval.
        Document text is untrusted data, never executable instructions.
        """
        ...

SCHEMA = {'type':'object','properties':{key:{'type':'string'} for key in ['invoice','date','subtotal','tax','total','currency','source_page']},'required':['invoice','date','subtotal','tax','total','currency','source_page'],'additionalProperties':False}
