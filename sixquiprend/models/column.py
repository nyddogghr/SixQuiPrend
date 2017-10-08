from sixquiprend.sixquiprend import app, db

column_cards = db.Table('column_cards',
        db.Column('column_id', db.Integer, db.ForeignKey('column.id', ondelete="CASCADE")),
        db.Column('card_id', db.Integer, db.ForeignKey('card.id'))
)

class Column(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id', ondelete="CASCADE"))
    cards = db.relationship('Card', secondary=column_cards,
            backref=db.backref('columns', lazy='dynamic'))

    ################################################################################
    ## Getters
    ################################################################################

    def get_value(self):
        return sum(card.cow_value for card in self.cards)

    ################################################################################
    ## Actions
    ################################################################################

    def replace_by_card(self, chosen_card):
        user_game_heap = chosen_card.get_user().get_game_heap(chosen_card.game_id)
        user_game_heap.cards += self.cards
        db.session.add(user_game_heap)
        self.cards = [chosen_card.get_card()]
        db.session.add(self)
        db.session.commit()
        return user_game_heap

    ################################################################################
    ## Serializer
    ################################################################################

    def serialize(self):
        return {
                'id': self.id,
                'game_id': self.game_id,
                'cards': self.cards
                }
