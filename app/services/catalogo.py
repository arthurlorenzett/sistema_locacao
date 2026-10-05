"""Como os espaços aparecem nas listagens (catálogo, favoritos, meus espaços)."""

from app.models.favorito_model import Favorito
from app.services import agenda, avaliacoes


def ids_favoritos(locatario_id) -> set:
    """Ids dos espaços favoritados pelo locatário."""
    return {f.espaco_id for f in Favorito.query.filter_by(locatario_id=locatario_id).all()}


def dict_catalogo(espaco, favoritos=frozenset()) -> dict:
    """Dados do espaço + favorito + horário livre hoje + média das avaliações."""
    return dict(espaco.to_dict(), favorito=espaco.id in favoritos, livre_hoje=agenda.livre_hoje(espaco),
                **avaliacoes.resumo_do_espaco(espaco.id))
