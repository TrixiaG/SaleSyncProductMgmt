from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, send_file, current_app
from .models import prodInventory, User  # Adjust this import based on your project structure
from . import db
from datetime import datetime, time
from flask_login import login_required, current_user

#for pdf generating
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

inventory = Blueprint('inventory', __name__)

@inventory.route('/inventory', methods=['GET', 'POST'])
@login_required
def prodInventoryView():
    products = prodInventory.query.all() 

    if current_user.access == 'Pending':
        flash('You are not authorized to view this page.', category='error')
        return render_template("restricted.html", boolean=True)
    
    if current_user == 'Deactivated':
        flash('You are not authorized to view this page.', category='error')
        return render_template("restricted.html", boolean=True)


    else:
        return render_template("inventory.html",products=products, current_user=current_user)
    


@inventory.route('/inventory/add_product', methods=['POST'])
@login_required
def addprod():
    try:
        data = request.get_json()

        ptype = data.get('prodType', '').strip()
        pcode = data.get('prodCode', '').strip()
        pname = data.get('prodName', '').strip()
        pstock = data.get('prodStock', '').strip()
        pprice = data.get('prodPrice', '').strip()

        # Convert pstock to int and pprice to float
        try:
            pstock = int(pstock)
        except ValueError:
            pstock = 0

        try:
            pprice = float(pprice)
        except ValueError:
            pprice = 0.0

        # Get current time and user ID
        ptimelog = datetime.utcnow()
        puserlog = current_user.eid

        # Check if product with pname already exists
        existing_product = prodInventory.query.filter_by(pname=pname).first()

        if existing_product:
            # Update existing product details
            existing_product.ptype = ptype
            existing_product.pcode = pcode
            existing_product.pstock = pstock
            existing_product.ptimelog = ptimelog
            existing_product.puserlog = puserlog
            existing_product.pprice = pprice
        else:
            # Create new product
            new_product = prodInventory(
                ptype=ptype,
                pcode=pcode,
                pname=pname,
                pstock=pstock,
                ptimelog=ptimelog,
                puserlog=puserlog,
                pprice=pprice
            )
            db.session.add(new_product)

        # Commit changes to the database
        db.session.commit()

        return jsonify({'status': 'success'}), 200

    except Exception as e:
        # Rollback transaction on error
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
# ...

@inventory.route('/inventory/search', methods=['POST'])
@login_required
def search_products():
    try:
        data = request.json
        search_term = data.get('searchTerm', '').strip()

        if not search_term:
            return jsonify({'status': 'error', 'message': 'Search term not provided.'}), 400

        products = prodInventory.query.filter(
                (prodInventory.pname.ilike(f'%{search_term}%')) |
                (prodInventory.pcode.ilike(f'%{search_term}%')) |
                (prodInventory.ptype.ilike(f'%{search_term}%'))
        ).all()

        if products:
            response_data = []
            for product in products:
                response_data.append({
                    'prodType': product.ptype,
                    'prodCode': product.pcode,
                    'prodName': product.pname,
                    'prodStock': product.pstock,
                    'prodPrice': product.pprice
                })

            return jsonify({'status': 'success', 'results': response_data}), 200
        else:
            return jsonify({'status': 'error', 'message': 'No products found.'}), 404

    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Error searching products: {str(e)}"}), 500
    

#DELETE PRODUCT
@inventory.route('/inventory/delete_product/<prodCode>', methods=['DELETE'])
@login_required
def delete_product(prodCode):
    try:
        product = prodInventory.query.filter_by(pcode=prodCode).first()

        if product:
            db.session.delete(product)
            db.session.commit()  # Commit the transaction
            return jsonify({'status': 'success', 'message': 'Product deleted successfully.'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Product not found.'}), 404

    except Exception as e:
        db.session.rollback()  # Rollback the transaction on error
        return jsonify({'status': 'error', 'message': f"Error deleting product: {str(e)}"}), 500
    
#update product
@inventory.route('/inventory/update_product', methods=['POST'])
@login_required
def update_product():
    try:
        data = request.json
        prodCode = data.get('prodCode')

        # Fetch existing product by prodCode
        product = prodInventory.query.filter_by(pcode=prodCode).first()

        if product:
            # Update existing product details
            product.ptype = data.get('prodType')
            product.pname = data.get('prodName')
            product.pstock = data.get('prodStock')
            product.pprice = data.get('prodPrice')
            product.ptimelog = datetime.utcnow()
            product.puserlog = current_user.eid

            db.session.commit()

            return jsonify({'status': 'success'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Product not found.'}), 404

    except Exception as e:
        db.session.rollback()  # Rollback the transaction on error
        return jsonify({'status': 'error', 'message': f"Error updating product: {str(e)}"}), 500
    
# Route to search product by code
@inventory.route('/inventory/search_by_code', methods=['POST'])
@login_required
def search_by_code():
    try:
        data = request.json
        prodCode = data.get('prodCode')

        if not prodCode:
            return jsonify({'status': 'error', 'message': 'Product code not provided.'}), 400

        product = prodInventory.query.filter_by(pcode=prodCode).first()

        if product:
            response_data = {
                'status': 'success',
                'prodType': product.ptype,
                'prodName': product.pname,
                'prodStock': product.pstock,
                'prodPrice' : product.pprice

            }
            return jsonify(response_data), 200
        else:
            return jsonify({'status': 'error', 'message': 'Product not found.'}), 404

    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Error searching product: {str(e)}"}), 500


# Route to search product by name
@inventory.route('/inventory/search_by_name', methods=['POST'])
@login_required
def search_by_name():
    try:
        data = request.json
        prodName = data.get('prodName')

        if not prodName:
            return jsonify({'status': 'error', 'message': 'Product name not provided.'}), 400

        product = prodInventory.query.filter_by(pname=prodName).first()

        if product:
            response_data = {
                'status': 'success',
                'prodType': product.ptype,
                'prodCode': product.pcode,
                'prodStock': product.pstock,
                'prodName': product.pname,
                'prodPrice' : product.pprice
            }
            return jsonify(response_data), 200
        else:
            return jsonify({'status': 'error', 'message': 'Product not found.'}), 404

    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Error searching product: {str(e)}"}), 500

@inventory.route('/inventory/pdf', methods=['POST'])
def generate_pdf():
    try:
        printdata = request.json
        print_option = printdata.get('printOption', 'all')  # Default to 'all' if printOption is not provided

        # Logging to debug
        print(f"Received printOption: {print_option}")

        if print_option not in ['all', 'available', 'unavailable']:
            return jsonify({'status': 'error', 'message': 'Invalid print option.'}), 400

        # Assuming prodInventory is your SQLAlchemy model
        inventory_data = prodInventory.query.all()  # Adjust query as per your needs

        if print_option == 'available':
            products = [item for item in inventory_data if item.status == 'Available']
            title = 'Available Products'
            show_totals = True
        elif print_option == 'unavailable':
            products = [item for item in inventory_data if item.status == 'Unavailable']
            title = 'Unavailable Products'
            show_totals = True

        else:
            products = inventory_data
            title = 'All Products'
            show_totals = True

        if show_totals:
            total_available_stock = sum(product.pstock for product in products if product.status == 'Available')
            total_unavailable_stock = sum(product.pstock for product in products if product.status == 'Unavailable')

        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        fileName = f"TCFM_Inventory_Report_{current_time}.pdf"

        total_stock = 0 
        total_available_stock = 0
        total_unavailable_stock = 0

        for product in products:
            total_stock += product.pstock
            if product.status == 'Available':
                total_available_stock += product.pstock
            elif product.status == 'Unavailable':
                total_unavailable_stock += product.pstock

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        pdf.setTitle(title)

        pagewidth = pdf._pagesize[0]

        pdf.setFont('Helvetica-Bold', 16)
        pdf.drawCentredString(300, 750, "THE CRAZY FISH MAN")
        pdf.setFont('Helvetica', 12)
        pdf.drawCentredString(300, 730, "Inventory Report")
        pdf.drawCentredString(300, 715, title)
        pdf.setFont('Helvetica', 10)
        pdf.drawString(50, 20, f"Report Generated at {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
        pdf.drawRightString(pagewidth - 20, 20, f"Report Generated by {current_user.first_name} {current_user.last_name} ({current_user.eid})")

        pdf.setFont('Helvetica-Bold', 12)
        if print_option == 'all':
            headers = ['Product Type', 'Product Code', 'Product Name', 'Stock', 'Price', 'Status']
            col_widths = [100, 100, 150, 40, 40, 70]
        else:
            headers = ['Product Type', 'Product Code', 'Product Name', 'Stock', 'Price']
            col_widths = [100, 100, 200, 50, 50]

        data = [headers]
        for product in products:
            if print_option == 'all':
                data.append([
                    product.ptype,
                    product.pcode,
                    product.pname,
                    str(product.pstock),
                    str(product.pprice),
                    product.status
                ])
            else:
                data.append([
                    product.ptype,
                    product.pcode,
                    product.pname,
                    str(product.pstock),
                    str(product.pprice)
                ])

        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ]))

        table.wrapOn(pdf, 425, 550)
        table.drawOn(pdf, 60, 500)

        pdf.setFont('Helvetica-Bold', 12)

        if show_totals:
            pdf.setFont('Helvetica-Bold', 12)
            pdf.drawString(60, 480, f"Total Stocks: {total_stock}")
            if print_option == 'all':
                pdf.drawString(60, 465, f"Total Available Stocks: {total_available_stock}")
                pdf.drawString(60, 450, f"Total Unavailable Stocks: {total_unavailable_stock}")

        pdf.save()

        buffer.seek(0)
        return send_file(buffer, download_name=fileName, as_attachment=True, mimetype='application/pdf')

    except Exception as e:
        return jsonify({'status': 'error', 'message': f"An error occurred while generating the PDF: {str(e)}"}), 500


@inventory.route('/inventory/addreducestocks', methods=['POST'])
@login_required
def add_reduce_stocks():
    try:
        data = request.json 

        prodCode = data.get('prodCode')
        additionalStock = data.get('additionalStock')
        prodPrice = data.get('prodPrice')

        product = prodInventory.query.filter_by(pcode=prodCode).first()

        if product:
            product.pstock += int(additionalStock)
            product.ptimelog = datetime.utcnow()
            product.puserlog = current_user.eid
            if prodPrice:
                product.pprice = float(prodPrice)

            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Stocks updated successfully.'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Product not found.'}), 404

    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Error updating stocks: {str(e)}"}), 500
    
@inventory.route('/inventory/toggle_status', methods=['POST'])
@login_required
def toggle_status():
    try:
        data = request.get_json()
        pcode = data.get('pcode')
        product = prodInventory.query.filter_by(pcode=pcode).first()

        if product:
            product.status = 'Unavailable' if product.status == 'Available' else 'Available'
            product.ptimelog = datetime.utcnow()
            product.puserlog = current_user.eid
            db.session.commit()
            return jsonify({'status': 'success'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Product not found.'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f"Error updating status: {str(e)}"}), 500
