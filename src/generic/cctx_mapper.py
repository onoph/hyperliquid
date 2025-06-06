import logging
import dacite
from dacite import Config
from dacite.data import Data
from typing import TypeVar, Type, Dict, Any, Optional, cast, List
import inspect
from dataclasses import fields, is_dataclass
import typing
import numbers

from src.generic.cctx_balance_model import AccountData
from src.generic.cctx_model import Order

logger = logging.getLogger(__name__)

def parse_order(api_data) -> Order:
    # Définir les valeurs par défaut pour les champs obligatoires
    defaults = {"info.coin": ""}
    return safe_parse(Order, api_data, defaults)

def parse_balance(api_data) -> AccountData:
    return safe_parse(AccountData, api_data)


T = TypeVar('T')

import dacite
from dacite import Config, from_dict
from typing import TypeVar, Type, Dict, Any, Optional, cast, get_origin, get_args
from dataclasses import fields, is_dataclass, MISSING
import inspect

T = TypeVar('T')


def safe_parse(data_class: Type[T], data: Dict[str, Any], default_values: Optional[Dict] = None) -> T:
    """
    Fonction générique pour parser de façon sécurisée les données API vers des classes dataclass.
    Gère automatiquement les structures imbriquées et champs manquants.
    """
    # Copie des données pour ne pas modifier l'original
    processed_data = {} if data is None else data.copy()

    try:
        logger.debug(f"[MAPPER] Tentative de parsing {data_class.__name__} avec data={processed_data}")
        return from_dict(
            data_class=data_class,
            data=processed_data,
            config=_create_config()
        )
    except dacite.exceptions.MissingValueError as e:
        logger.debug(f"[MAPPER] MissingValueError: {e}")
        # Si erreur, récupérer le chemin du champ manquant
        field_path = str(e).split("missing value for field ")[-1].strip('"')

        # Compléter les structures imbriquées au besoin
        _ensure_nested_path(processed_data, field_path)

        # Appliquer les valeurs par défaut spécifiées
        if default_values:
            for key, value in default_values.items():
                _set_nested_value(processed_data, key, value)

        # Remplir automatiquement les champs manquants avec des valeurs vides
        _fill_missing_fields(data_class, processed_data)

        logger.debug(f"[MAPPER] Nouvelle tentative de parsing {data_class.__name__} avec data={processed_data}")
        return from_dict(
            data_class=data_class,
            data=processed_data,
            config=_create_config()
        )


def _safe_float(x):
    try:
        return 0.0 if x is None or x == "" else float(x)
    except (ValueError, TypeError):
        logger.debug(f"[MAPPER] Fallback float pour valeur: {x!r}")
        return 0.0

def _safe_int(x):
    try:
        return 0 if x is None or x == "" else int(x)
    except (ValueError, TypeError):
        logger.debug(f"[MAPPER] Fallback int pour valeur: {x!r}")
        return 0

def _safe_bool(x):
    try:
        return False if x is None or x == "" else bool(x)
    except (ValueError, TypeError):
        logger.debug(f"[MAPPER] Fallback bool pour valeur: {x!r}")
        return False

def _create_config():
    """Crée une configuration dacite avec des hooks de type sécurisés"""
    return Config(
        type_hooks={
            str: lambda x: "" if x is None else str(x),
            float: _safe_float,
            int: _safe_int,
            bool: _safe_bool,
            List[Any]: lambda x: x if isinstance(x, list) else [] if x is None else [x]
        },
        strict=False,
        cast=[tuple]  # Enlever list du cast pour éviter la conversion automatique
    )


def _ensure_nested_path(data: Dict[str, Any], path: str):
    """Crée les structures imbriquées nécessaires pour un chemin donné"""
    parts = path.split('.')
    current = data

    for i, part in enumerate(parts):
        if part not in current:
            # Si c'est le dernier élément, mettre une valeur adaptée
            if i == len(parts) - 1:
                if part == "timestamp":
                    current[part] = 0
                else:
                    current[part] = ""
            else:
                current[part] = {}
        elif i < len(parts) - 1 and not isinstance(current[part], dict):
            # Remplacer une valeur non-dict par un dict si nécessaire
            current[part] = {}

        if i < len(parts) - 1:
            current = current[part]


def _set_nested_value(data: Dict[str, Any], path: str, value: Any):
    parts = path.split('.')
    current = data
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]
    # N'écrase pas si déjà présent et non None
    if parts[-1] not in current or current[parts[-1]] is None:
        current[parts[-1]] = value


def _is_list_type(field_type):
    """Vérifie si un type est un type de liste (List[Any], List[str], etc.)"""
    origin = typing.get_origin(field_type)
    return origin is list or field_type is list


def _is_type(field_type, target_type):
    origin = typing.get_origin(field_type)
    args = typing.get_args(field_type)
    if origin is None:
        return field_type == target_type
    return target_type in args


def _resolve_type(field_type):
    """Retourne la liste plate de tous les types de base d'un type (gère Union, Optional, etc.)"""
    origin = typing.get_origin(field_type)
    args = typing.get_args(field_type)
    if origin is None:
        return [field_type]
    types = []
    for arg in args:
        types.extend(_resolve_type(arg))
    return types


def _fill_missing_fields(data_class: Type, data: Dict[str, Any], prefix: str = ""):
    """Remplit récursivement tous les champs manquants dans un dataclass"""
    if not is_dataclass(data_class):
        return

    for field in fields(data_class):
        field_path = f"{prefix}{field.name}" if prefix else field.name
        parts = field_path.split('.')

        # Vérifier si le champ existe déjà dans les données
        target = data
        exists = True
        for i, part in enumerate(parts):
            if part not in target:
                exists = False
                break
            if i < len(parts) - 1:
                if not isinstance(target[part], dict):
                    target[part] = {}
                target = target[part]

        # Ne remplit que si la valeur n'existe pas ou est None
        if not exists or (exists and target.get(parts[-1], None) is None):
            # D'abord vérifier si c'est un type liste directement
            if _is_list_type(field.type):
                _set_nested_value(data, field_path, [])
                continue
                
            base_types = _resolve_type(field.type)
            
            # Ensuite vérifier les autres types
            if any(isinstance(t, type) and issubclass(t, numbers.Integral) and t is not bool for t in base_types):
                _set_nested_value(data, field_path, 0)
            elif any(isinstance(t, type) and issubclass(t, numbers.Real) and t is not bool for t in base_types):
                _set_nested_value(data, field_path, 0.0)
            elif any(t is bool for t in base_types):
                _set_nested_value(data, field_path, False)
            else:
                _set_nested_value(data, field_path, "")

        # Traitement récursif pour les dataclasses imbriquées
        if is_dataclass(field.type):
            nested_target = data
            for part in parts[:-1]:
                if part not in nested_target:
                    nested_target[part] = {}
                nested_target = nested_target[part]

            if parts[-1] not in nested_target:
                nested_target[parts[-1]] = {}

            _fill_missing_fields(field.type, nested_target[parts[-1]], "")