import databases
import sqlalchemy as sa

DATABASE_URL = "sqlite:///./db.sqlite3"

database = databases.Database(DATABASE_URL)

metadata = sa.MetaData()


user = sa.Table(
    "user",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("name", sa.String),
    sa.Column("avatar", sa.String, nullable=True),
    sa.Column("email", sa.String, unique=True),
    sa.Column("password", sa.String),
    sa.Column("created_at", sa.DateTime),
)

task = sa.Table(
    "task",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("name", sa.String),
    sa.Column("user_id", sa.ForeignKey("user.id"), nullable=True),
    sa.Column("description", sa.String, nullable=True),
    sa.Column("completed", sa.Boolean),
)


checkbox = sa.Table(
    "checkbox",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("name", sa.String),
    sa.Column("task_id", sa.ForeignKey("task.id"), nullable=True),
    sa.Column("completed", sa.Boolean),
)

engine = sa.create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
