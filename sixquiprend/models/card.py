from sixquiprend.models.six_qui_prend_exception import SixQuiPrendException
from sixquiprend.sixquiprend import app, db

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    cow_value = db.Column(db.Integer, nullable=False)

    ################################################################################
    ## Getters
    ################################################################################

    def find(card_id):
        card = Card.query.get(card_id)
        if not card:
            raise SixQuiPrendException('Card doesn\'t exist', 404)
        return card

    ################################################################################
    ## Serializer
    ################################################################################

    def serialize(self):
        return {
                'id': self.id,
                'number': self.number,
                'cow_value': self.cow_value
                }
