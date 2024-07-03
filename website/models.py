#database models
from . import db
from flask_login import UserMixin
from datetime import datetime 
from flask_migrate import Migrate


class User(db.Model, UserMixin):
    eid = db.Column(db.String(8), primary_key=True, unique=True, nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    bday = db.Column(db.String(150), nullable=False)
    access = db.Column(db.String(150), nullable=False)

    def get_id(self):
        return self.eid

class UserUpdateLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    eid = db.Column(db.String(8), nullable=False)
    field_updated = db.Column(db.String(50), nullable=False)
    updated_by = db.Column(db.String(50), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __init__(self, eid, field_updated, updated_by):
        self.eid = eid
        self.field_updated = field_updated
        self.updated_by = updated_by
        self.updated_at = datetime.utcnow()



class prodInventory(db.Model):
    ptype = db.Column(db.String(50), nullable=False)
    pcode = db.Column(db.String(50), primary_key=True, nullable=False)
    pname = db.Column(db.String(50), unique=True, nullable=False)
    pstock = db.Column(db.Integer, default=0, nullable=False)
    ptimelog = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    puserlog = db.Column(db.String(50), nullable=False)
    pprice = db.Column(db.Numeric(10, 2), default=0)

    def __init__(self, ptype, pcode, pname, pstock, ptimelog, puserlog, pprice):
        self.ptype = ptype
        self.pcode = pcode
        self.pname = pname
        self.pstock = pstock
        self.ptimelog = ptimelog
        self.puserlog = puserlog
        self.pprice = pprice

    def update_stock(self, quantity):
        if self.pstock >= quantity:
            self.pstock -= quantity
        else:
            raise ValueError("Insufficient stock")

class Transaction(db.Model):
    transaction_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), default=0)
    

    items = db.relationship('IndivTransaction', back_populates='transaction', cascade='all, delete-orphan')

    def __init__(self, total_amount):
        self.transaction_date = datetime.utcnow()
        self.total_amount = total_amount

class IndivTransaction(db.Model):
    item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.transaction_id'))
    product_id = db.Column(db.String(50), db.ForeignKey('prod_inventory.pcode'))
    quantity = db.Column(db.Integer)
    unit_price = db.Column(db.Numeric(10, 2))
    total_price = db.Column(db.Numeric(10, 2))

    transaction = db.relationship('Transaction', back_populates='items')
    product = db.relationship('prodInventory')

    def __init__(self, transaction_id, product_id, quantity, unit_price):
        self.transaction_id = transaction_id
        self.product_id = product_id
        self.quantity = quantity
        self.unit_price = unit_price
        self.total_price = quantity * unit_price

class TransactionReceipt(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.transaction_id'), nullable=False)
    filename = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    tuserlog = db.Column(db.String(8), db.ForeignKey('user.eid'), nullable=False)

    transaction = db.relationship('Transaction')
    user = db.relationship('User')
    def __init__(self, transaction_id, filename, tuserlog):
        self.transaction_id = transaction_id
        self.filename = filename
        self.created_at = datetime.utcnow()
        self.tuserlog = tuserlog

    @property
    def formatted_created_at(self):
        return self.created_at.date() 
    
    def __repr__(self):
        return f"<TransactionReceipt {self.id}>"