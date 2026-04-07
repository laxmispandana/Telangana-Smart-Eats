from app import create_app
from app.services.data_seed import seed_data


app = create_app()


if __name__ == "__main__":
    with app.app_context():
        seed_data()
        print("Image refresh completed.")
