from sixquiprend.sixquiprend import app, db
from sixquiprend.models.card import Card

class ChosenCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"))
    game_id = db.Column(db.Integer, db.ForeignKey('game.id', ondelete="CASCADE"))
    card_id = db.Column(db.Integer, db.ForeignKey('card.id'))

    ################################################################################
    ## Getters
    ################################################################################

    def get_user(self):
        return User.query.get(self.user_id)

    def get_card(self):
        return Card.query.get(self.card_id)

    ################################################################################
    ## Serializer
    ################################################################################

    def serialize(self):
        return {
                'id': self.id,
                'user_id': self.user_id,
                'game_id': self.game_id,
                'card': self.get_card()
                }
