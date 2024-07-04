from flask import Blueprint, render_template, request, jsonify, send_file, current_app,flash
from .models import Transaction, IndivTransaction, prodInventory, User, UserUpdateLog, TransactionReceipt, db
from flask_login import current_user, login_required
from datetime import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import os
import io
from flask import redirect, url_for

cashierops = Blueprint('cashierops', __name__)

@cashierops.route('/cashier-ops', methods=['GET', 'POST'])
@login_required
def user_cashier():
    
    logged_in_user = current_user.first_name  
    current_date = datetime.now().strftime("%Y-%m-%d")

    if User.access == 'Pending':
        flash('You are not authorized to view this page.', category='error')
        return render_template("restricted.html", boolean=True)

    if current_user == 'Deactivated':
        flash('You are not authorized to view this page.', category='error')
        return render_template("restricted.html", boolean=True)

    else:
        return render_template("cashierops.html", boolean=True, user_logged=logged_in_user, date=current_date, current_user=current_user)

@cashierops.route('/get-product-details/<productCode>', methods=['GET'])
@login_required
def get_product_details(productCode):
    try:
        product = prodInventory.query.filter_by(pcode=productCode).first()
        if not product:
            return jsonify({"error": f"Product with code {productCode} not found"}), 404
        
        return jsonify({
            "pname": product.pname,
            "pprice": str(product.pprice),
            "ptype": product.ptype,
            "pcode": product.pcode
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@cashierops.route('/void_transaction/<int:transaction_id>', methods=['POST'])
def void_transaction(transaction_id):
    indiv_transaction = IndivTransaction.query.filter_by(transaction_id=transaction_id).first()
    if indiv_transaction:
        indiv_transaction.mark_as_void()
        # Add logic to update stock if necessary
        # Example: indiv_transaction.product.update_stock(indiv_transaction.quantity)
        db.session.commit()
        flash('Transaction voided successfully.', 'success')
    else:
        flash('Transaction not found.', 'error')
    return redirect(url_for('view_transactions'))  # Redirect to your transactions view

@cashierops.route('/get-product-types', methods=['GET'])
@login_required
def get_product_types():
    try:
        product_types = db.session.query(prodInventory.ptype).distinct().all()
        types_list = [ptype[0] for ptype in product_types]
        return jsonify({"product_types": types_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to get product names by product type
@cashierops.route('/get-product-names/<productType>', methods=['GET'])
@login_required
def get_product_names(productType):
    try:
        products = prodInventory.query.filter_by(ptype=productType).all()
        names_list = [{"name": product.pname, "code": product.pcode} for product in products]
        return jsonify({"product_names": names_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Route to create a new transaction
@cashierops.route('/create-transaction', methods=['POST'])
@login_required
def create_transaction():
    try:
        new_transaction = Transaction(total_amount=0)
        db.session.add(new_transaction)
        db.session.commit()
        
        return jsonify({
            "message": "Transaction created successfully", 
            "transaction_id": new_transaction.transaction_id
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

# Route to add a product to a transaction
@cashierops.route('/add-product-to-transaction', methods=['POST'])
@login_required
def add_product_to_transaction():
    data = request.json
    try:
        transaction_id = data.get('transaction_id')
        product_id = data.get('product_id')
        quantity = data.get('quantity')
        
        transaction = Transaction.query.get(transaction_id)
        product = prodInventory.query.filter_by(pcode=product_id).first()
        
        if not transaction or not product:
            raise ValueError("Invalid transaction or product ID")
        
        total_price = quantity * product.pprice
        
        transaction_item = IndivTransaction(
            transaction_id=transaction_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=product.pprice
        )
        
        db.session.add(transaction_item)
        
        transaction.total_amount += total_price
        
        product.update_stock(quantity)
        
        db.session.commit()
        
        return jsonify({"message": "Product added successfully"}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

# Route to get transaction details by transaction ID
@cashierops.route('/get-transaction-details/', methods=['GET'])
@login_required
def get_transaction_details():
    transaction_id = request.args.get('transaction_id')
    
    try:
        transaction = Transaction.query.get(transaction_id)
        
        if not transaction:
            raise ValueError("Invalid transaction ID")
        
        items = IndivTransaction.query.filter_by(transaction_id=transaction_id).all()
        item_details = [{
            'product_id': item.product_id,
            'quantity': item.quantity,
            'unit_price': item.unit_price,
            'total_price': item.quantity * item.unit_price
        } for item in items]
        
        return jsonify({
            'transaction_id': transaction_id,
            'total_amount': transaction.total_amount,
            'items': item_details
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# Route to reset a transaction
@cashierops.route('/reset_transaction', methods=['DELETE'])
@login_required
def reset_transaction():
    try:
        current_transaction = Transaction.query.order_by(Transaction.transaction_id.desc()).first()

        if current_transaction:
            items_to_delete = IndivTransaction.query.filter_by(transaction_id=current_transaction.transaction_id).all()

            if items_to_delete:
                for item in items_to_delete:
                    product_inventory = prodInventory.query.filter_by(pcode=item.product_id).first()
                    if product_inventory:
                        product_inventory.pstock += item.quantity 
                        db.session.delete(item)  
                    else:
                        db.session.rollback()
                        return jsonify({'status': 'error', 'message': 'Product not found in inventory.'}), 404

                current_transaction.total_amount  = 0
                db.session.commit()

                return jsonify({'status': 'success', 'message': 'Transaction reset successfully.'}), 200
            else:
                return jsonify({'status': 'error', 'message': 'No items found in current transaction.'}), 404
        else:
            return jsonify({'status': 'error', 'message': 'No active transaction found.'}), 404

    except Exception as e:
        current_app.logger.error(f"Error resetting transaction: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'Internal Server Error. Please try again later.'}), 500

# Route to remove a product from a transaction    
@cashierops.route('/inventory/delete_product/<prodCode>', methods=['DELETE'])
@login_required
def delete_product(prodCode):
    try:
        current_transaction = Transaction.query.order_by(Transaction.transaction_id.desc()).first()

        if current_transaction:
            item_to_delete = IndivTransaction.query.filter_by(transaction_id=current_transaction.transaction_id, product_id=prodCode).first()

            if item_to_delete:
                current_app.logger.debug(f"Item to delete: {item_to_delete.product_id}, Quantity: {item_to_delete.quantity}, Unit Price: {item_to_delete.unit_price}")

                current_transaction.total_amount -= (item_to_delete.quantity * item_to_delete.unit_price)

                product_inventory = prodInventory.query.filter_by(pcode=prodCode).first()
                if product_inventory:
                    current_app.logger.debug(f"Product Inventory before update: {product_inventory.pcode}, Stock: {product_inventory.pstock}")

                    product_inventory.pstock += (item_to_delete.quantity)/2

                    current_app.logger.debug(f"Product Inventory after update: {product_inventory.pcode}, Updated Stock: {product_inventory.pstock}")
                else:
                    return jsonify({'status': 'error', 'message': 'Product not found in inventory.'}), 404

                db.session.delete(item_to_delete)
                db.session.commit()
                return jsonify({'status': 'success', 'message': 'Product deleted successfully.'}), 200
            else:
                return jsonify({'status': 'error', 'message': 'Product not found in current transaction.'}), 404
        else:
            return jsonify({'status': 'error', 'message': 'No active transaction found.'}), 404

    except Exception as e:
        current_app.logger.error(f"Error deleting product: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Internal Server Error. Please try again later.'}), 500


    

@cashierops.route('/cashierops/pdf', methods=['POST'])
@login_required
def generate_pdf():
    data = request.get_json()

    if 'transaction_id' not in data:
        return jsonify({'error': 'Transaction ID not provided'}), 400

    transaction_id = data['transaction_id']

    transaction = Transaction.query.get(transaction_id)

    if not transaction:
        return jsonify({'error': 'Transaction not found'}), 404

    items = IndivTransaction.query.filter_by(transaction_id=transaction_id).all()
    if not items:
        return jsonify({'error': 'No items found for this transaction'}), 404

    current_time = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    pdf_filename = f"TCFM_TransactionNo._{transaction_id}.pdf"

    documentTitle = f'TCFM Transaction Receipt {transaction_id}'
    subTitle = f"Transaction Completed at {current_time}"
    subTitle2 = f"Staff: {current_user.first_name} {current_user.last_name} ({current_user.eid})"
    transactionno = f"Transaction No. {transaction_id}"

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)

    pdf.setTitle(documentTitle)
    pdf.setFont('Helvetica-Bold', 12)
    pdf.drawCentredString(300, 750, "THE CRAZY FISH MAN")
    pdf.drawCentredString(300, 735, transactionno)
    pdf.setFont('Helvetica', 10)
    pdf.drawCentredString(300, 700, subTitle)
    pdf.drawCentredString(300, 690, subTitle2)
    pdf.setFont('Helvetica-Bold', 10)

    y_position = 600

    data = [['Product Type', 'Product Code', 'Product Name', 'Unit Price', 'Amount']]

    for item in items:
        product = prodInventory.query.get(item.product_id)
        if product:
            unit_price = product.pprice
            amount = item.quantity * unit_price
            data.append([
                product.ptype,
                product.pcode,
                product.pname,
                f"P{unit_price:.2f}",
                f"P{amount:.2f}"
            ])

    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
    ])

    column_widths = [100, 100, 150, 50, 100] 

    table = Table(data, colWidths=column_widths)
    table.setStyle(table_style)
    
    table.wrapOn(pdf, 500, 580)
    table.drawOn(pdf, 72, 580)

    total_amount = sum(item.quantity * prodInventory.query.get(item.product_id).pprice for item in items)
    pdf.setFont('Helvetica-Bold', 13)
    pdf.drawString(400, y_position - len(data) * 20 - 20, f"Total Amount: P{total_amount:.2f}")

    pdf.save()
    
    buffer.seek(0)

    receipts_folder = os.path.join(current_app.root_path, 'receipts')
    os.makedirs(receipts_folder, exist_ok=True)
    filepath = os.path.join(receipts_folder, pdf_filename)

    with open(filepath, 'wb') as f:
        f.write(buffer.getvalue())

    receipt = TransactionReceipt(transaction_id=transaction_id, filename=pdf_filename, tuserlog=current_user.eid)
    db.session.add(receipt)
    db.session.commit()

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"Receipt_{transaction_id}.pdf",
        mimetype='application/pdf'
    )