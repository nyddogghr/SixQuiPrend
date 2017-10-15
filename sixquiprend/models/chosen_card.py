from sixquiprend.sixquiprend import app, db

class ChosenCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"))
    game_id = db.Column(db.Integer, db.ForeignKey('game.id', ondelete="CASCADE"))
    card_id = db.Column(db.Integer, db.ForeignKey('card.id'))

    ################################################################################
    ## Serializer
    ################################################################################

    def serialize(self):
        from sixquiprend.models.card import Card
        return {
                'id': self.id,
                'user_id': self.user_id,
                'game_id': self.game_id,
                'card': Card.find(self.card_id)
                }
