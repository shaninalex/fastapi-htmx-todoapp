import databases
import sqlalchemy as sa

DATABASE_URL = "sqlite:///./test.db"

database = databases.Database(DATABASE_URL)

metadata = sa.MetaData()


user = sa.Table(
    "user",
    metadata,
    sa.Column("id", sqlalchemy.Integer, primary_key=True),
    sa.Column("name", sqlalchemy.String),
    sa.Column("avatar", sqlalchemy.String, nullable=True),
    sa.Column("email", sqlalchemy.String),
    sa.Column("password", sqlalchemy.String),
    sa.Column("created_at", sqlalchemy.DateTime),
)

task = sa.Table(
    "task",
    metadata,
    sa.Column("id", sqlalchemy.Integer, primary_key=True),
    sa.Column("name", sqlalchemy.String),
    sa.Column("user_id", sa.ForeignKey("user.id"), nullable=True),
    sa.Column("description", sqlalchemy.String, nullable=True),
    sa.Column("completed", sqlalchemy.Boolean),
)


checkbox = sa.Table(
    "checkbox",
    metadata,
    sa.Column("id", sqlalchemy.Integer, primary_key=True),
    sa.Column("name", sqlalchemy.String),
    sa.Column("task_id", sa.ForeignKey("task.id"), nullable=True),
    sa.Column("completed", sqlalchemy.Boolean),
)
