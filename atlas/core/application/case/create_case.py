"""Application service for the Case use case (DO-IMP-001).

Only two operations are in scope: establishing a new Case, and
retrieving one by id. Creating a Case never creates any other Domain
Object — CaseService holds exactly one repository and nothing else, by
construction. Nothing outside this package's approved scope
(DO-IMP-002 onward) depends on Case yet.
"""
from __future__ import annotations

from atlas.core.domain.case.entity import Case
from atlas.core.domain.case.exceptions import CaseNotFoundError
from atlas.core.domain.case.repository import CaseRepository
from atlas.core.domain.case.value_objects import CaseId


class CaseService:
    def __init__(self, repository: CaseRepository) -> None:
        self._repository = repository

    def create(self) -> Case:
        case = Case.create()
        self._repository.add(case)
        return case

    def get(self, case_id: CaseId) -> Case:
        case = self._repository.get(case_id)
        if case is None:
            raise CaseNotFoundError(f"No Case found with id {case_id}")
        return case
