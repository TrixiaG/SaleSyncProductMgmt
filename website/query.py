from sqlalchemy import create_engine, func, and_
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from models import TransactionReceipt, db_connect, create_table

# Assuming you have SQLAlchemy models defined in 'models.py' and db_connect function to connect to your database

def remove_duplicates():
    # Connect to the database
    engine = db_connect()
    
    # Create a session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Subquery to get the most recent transaction receipts by transaction_id
        subquery = session.query(
            TransactionReceipt.transaction_id,
            func.max(TransactionReceipt.created_at).label('max_created_at')
        ).group_by(TransactionReceipt.transaction_id).subquery()

        # Query to select all duplicate entries
        duplicates = session.query(TransactionReceipt).\
            join(subquery, and_(
                TransactionReceipt.transaction_id == subquery.c.transaction_id,
                TransactionReceipt.created_at < subquery.c.max_created_at
            )).all()

        # Delete duplicate entries
        for duplicate in duplicates:
            session.delete(duplicate)
        
        # Commit the changes
        session.commit()
        
        print(f"Successfully removed {len(duplicates)} duplicate entries.")
    
    except Exception as e:
        session.rollback()
        print(f"Error occurred: {str(e)}")
    
    finally:
        session.close()

if __name__ == "__main__":
    remove_duplicates()
