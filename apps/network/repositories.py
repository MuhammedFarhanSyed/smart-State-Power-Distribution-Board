from typing import Optional, List, Dict, Any
from django.db import models
from django.db.models import QuerySet
from apps.network.models import Substation, Feeder, DistributionTransformer, Pole, Span


class SubstationRepository:
    """
    Repository encapsulating database access for Substations.
    """

    @staticmethod
    def get_by_id(substation_id: str) -> Optional[Substation]:
        """Fetch a single substation by its primary key."""
        try:
            return Substation.objects.get(substation_id=substation_id)
        except Substation.DoesNotExist:
            return None

    @staticmethod
    def list_all() -> QuerySet[Substation]:
        """Retrieve all substations ordered by ID."""
        return Substation.objects.all().order_by('substation_id')


class FeederRepository:
    """
    Repository encapsulating database access for Feeders.
    """

    @staticmethod
    def get_by_id(feeder_id: str) -> Optional[Feeder]:
        """Fetch a single feeder by ID, pre-fetching its parent substation."""
        try:
            return Feeder.objects.select_related('substation').get(feeder_id=feeder_id)
        except Feeder.DoesNotExist:
            return None

    @staticmethod
    def list_by_substation(substation_id: str) -> QuerySet[Feeder]:
        """Retrieve all feeders originating from a specific substation."""
        return Feeder.objects.filter(substation_id=substation_id).select_related('substation')


class TransformerRepository:
    """
    Repository encapsulating database access for Distribution Transformers.
    """

    @staticmethod
    def get_by_id(dt_id: str) -> Optional[DistributionTransformer]:
        """Fetch a single DT by ID, pre-fetching feeder and substation."""
        try:
            return DistributionTransformer.objects.select_related('feeder', 'feeder__substation').get(dt_id=dt_id)
        except DistributionTransformer.DoesNotExist:
            return None

    @staticmethod
    def list_by_feeder(feeder_id: str) -> QuerySet[DistributionTransformer]:
        """Retrieve all DTs attached to a specific 11kV feeder."""
        return DistributionTransformer.objects.filter(feeder_id=feeder_id).select_related('feeder')

    @staticmethod
    def list_all() -> QuerySet[DistributionTransformer]:
        """Retrieve all DTs across the subdivision."""
        return DistributionTransformer.objects.all().select_related('feeder')


class PoleRepository:
    """
    Repository encapsulating database access for Poles and radial topology lookups.
    """

    @staticmethod
    def get_by_id(pole_id: str) -> Optional[Pole]:
        """Fetch a single pole by ID, pre-fetching DT, Feeder, and Parent Pole."""
        try:
            return Pole.objects.select_related('dt', 'feeder', 'parent_pole').get(pole_id=pole_id)
        except Pole.DoesNotExist:
            return None

    @staticmethod
    def get_by_device_id(device_id: str) -> Optional[Pole]:
        """Lookup a pole by its attached telemetry IoT device ID."""
        try:
            return Pole.objects.select_related('dt', 'feeder', 'parent_pole').get(device_id=device_id)
        except Pole.DoesNotExist:
            return None

    @staticmethod
    def get_poles_by_dt(dt_id: str) -> QuerySet[Pole]:
        """
        Retrieve all poles under a given Distribution Transformer.
        Pre-fetches parent_pole for tree construction without N+1 queries.
        """
        return Pole.objects.filter(dt_id=dt_id).select_related('parent_pole', 'dt', 'feeder').order_by('seq_on_line', 'pole_id')

    @staticmethod
    def get_poles_by_feeder(feeder_id: str) -> QuerySet[Pole]:
        """Retrieve all poles under a given 11kV Feeder."""
        return Pole.objects.filter(feeder_id=feeder_id).select_related('dt', 'parent_pole')

    @staticmethod
    def get_unsequenced_poles_by_dt(dt_id: str) -> QuerySet[Pole]:
        """
        Retrieve poles under a DT that are missing topology data (missing parent_pole or seq_on_line).
        Used by the Missing Topology Inferencer.
        """
        return Pole.objects.filter(dt_id=dt_id).filter(
            models.Q(seq_on_line__isnull=True) | models.Q(parent_pole__isnull=True)
        ).select_related('dt')

    @staticmethod
    def bulk_update_parent_pointers(updates: List[Dict[str, Any]]) -> int:
        """
        Bulk update parent_pole pointers for inferred topology links.
        Expects a list of dicts: [{'pole_id': 'P-123', 'parent_pole_id': 'P-122', 'seq_on_line': 2}, ...]
        Returns count of updated records.
        """
        poles_to_update = []
        for update in updates:
            pole_id = update['pole_id']
            parent_id = update.get('parent_pole_id')
            seq = update.get('seq_on_line')

            pole = Pole(pole_id=pole_id)
            if parent_id:
                pole.parent_pole_id = parent_id
            if seq is not None:
                pole.seq_on_line = seq
            poles_to_update.append(pole)

        fields = []
        if any('parent_pole_id' in u for u in updates):
            fields.append('parent_pole')
        if any('seq_on_line' in u for u in updates):
            fields.append('seq_on_line')

        if not fields or not poles_to_update:
            return 0

        Pole.objects.bulk_update(poles_to_update, fields=fields, batch_size=500)
        return len(poles_to_update)


class SpanRepository:
    """
    Repository encapsulating database access for physical wire Spans.
    """

    @staticmethod
    def get_by_id(span_id: str) -> Optional[Span]:
        """Fetch a single span by ID, pre-fetching from_pole, to_pole, dt, feeder."""
        try:
            return Span.objects.select_related('from_pole', 'to_pole', 'dt', 'feeder').get(span_id=span_id)
        except Span.DoesNotExist:
            return None

    @staticmethod
    def get_by_poles(from_pole_id: str, to_pole_id: str) -> Optional[Span]:
        """Lookup a physical wire span by its connecting endpoints."""
        try:
            return Span.objects.select_related('from_pole', 'to_pole', 'dt', 'feeder').get(
                from_pole_id=from_pole_id,
                to_pole_id=to_pole_id
            )
        except Span.DoesNotExist:
            return None

    @staticmethod
    def list_by_dt(dt_id: str) -> QuerySet[Span]:
        """Retrieve all physical spans under a Distribution Transformer."""
        return Span.objects.filter(dt_id=dt_id).select_related('from_pole', 'to_pole', 'dt')

    @staticmethod
    def list_by_feeder(feeder_id: str) -> QuerySet[Span]:
        """Retrieve all physical spans under a Feeder."""
        return Span.objects.filter(feeder_id=feeder_id).select_related('from_pole', 'to_pole')
