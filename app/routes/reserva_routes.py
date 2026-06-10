from flask import Blueprint, request, jsonify
from app.facades.reserva_facade import ReservaFacade

# Cria um agrupamento de rotas para reservas
reserva_bp = Blueprint('reserva_bp', __name__)

@reserva_bp.route('/realizar', methods=['POST'])
def realizar_reserva():
    """
    Endpoint para que o Locatário solicite um agendamento.
    """
    dados = request.get_json()
    
    try:
        # A classe ReservaFacade reduz a complexidade da comunicação 
        # entre o frontend (Flet) e a lógica de negócios no backend[cite: 183].
        nova_reserva = ReservaFacade.realizar_reserva(
            locatario_id=dados.get('locatario_id'),
            espaco_id=dados.get('espaco_id'),
            data_horario=dados.get('data_horario')
        )
        
        return jsonify({
            "mensagem": "Pedido de reserva realizado com sucesso!",
            "reserva_id": nova_reserva.id,
            "status": nova_reserva.status_texto # Iniciará como Pendente devido ao padrão State [cite: 114, 153]
        }), 201
        
    except ValueError as e:
        # Retorna ao frontend caso o horário não esteja disponível
        return jsonify({"erro": str(e)}), 400