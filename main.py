# main.py
from app import create_app
from app.scheduler import scheduler  # ✅ Import the scheduler after app is created

app = create_app()

if __name__ == '__main__':
    scheduler.start()  # ✅ Start the background scheduler
    app.run(debug=True)
