from website.models import db, prodInventory


product_id = 'AQR001'  # Product ID to delete, adjust as needed

try:
    # Query the product by its product code
    product = prodInventory.query.filter_by(pcode=product_id).first()

    if product:
        # Delete the product from the database session
        db.session.delete(product)
        db.session.commit()
        print(f"Product with ID {product_id} deleted successfully.")
    else:
        print(f"Product with ID {product_id} not found.")
except Exception as e:
    print(f"Failed to delete product with ID {product_id}: {str(e)}")
    db.session.rollback()  # Rollback the session in case of error
finally:
    db.session.close()  # Close the session
