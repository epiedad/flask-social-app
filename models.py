import datetime
import os

from peewee import *

#Need to install this Foreign Function Interface
#because `pip install flask-bcrypt throws an error:
#'x86_64-linux-gnu-gcc' failed with exit
#sudo apt-get install libffi-dev

from flask_bcrypt import generate_password_hash
from flask_login import UserMixin

if 'HEROKU' in os.environ:
    import urlparse, psycopg2
    urlparse.uses_netloc.append('postgres')
    url = urlparse.urlparse(os.environ["DATABASE_URL"])
    psql_db = PostgresqlDatabase(database=url.path[1:], user=url.username, password=url.password, host=url.hostname, port=url.port)
else:
    psql_db = PostgresqlDatabase('dbtest', user='jelian', password='1234')

class User(UserMixin, Model):
    username = CharField(unique=True)
    email = CharField(unique=True)
    password = CharField(max_length=100)
    joined_at = DateTimeField(default=datetime.datetime.now)
    is_admin = BooleanField(default=False)

    class Meta:
        database = psql_db
        order_by = ('-joined_at',)
    
    def get_post(self):
        return Post.select().where(Post.user == self)

    def get_stream(self):
        return Post.select().where(
            (Post.user << self.following()) |
            (Post.user == self)
        )
    
    def following(self):
        """The users that we are following"""
        return (
            User.select().join(
                Relationship, on=Relationship.to_user
            ).where(
                Relationship.from_user == self
            )
        )

    def followers(self):
        """Get users following the curent user"""
        return(
            User.select().join(
                Relationship, on=Relationship.from_user
            ).where(
                Relationship.to_user == self
            )
        )

    @classmethod
    def create_user(cls, username, email, password, admin=False):
        password.encode('utf-8')
        try:
            with psql_db.transaction():
                cls.create(
                        username=username,
                        email=email,
                        password=generate_password_hash(password),
                        is_admin=admin
                )
        except IntegrityError:
            raise ValueError("User already exists")

class Relationship(Model):
    from_user = ForeignKeyField(User, related_name="relationships")
    to_user = ForeignKeyField(User, related_name="related_to")

    class Meta:
        database = psql_db
        indexes = (
                (('from_user', 'to_user'), True )
        )

class Post(Model):
    timestamp = DateTimeField(default=datetime.datetime.now)
    user = ForeignKeyField(
            rel_model=User,
            related_name='posts'
    )
    content = TextField()

    class Meta:
        database = psql_db
        order_by = ('-timestamp',)

def initialize():
    psql_db.connect()
    psql_db.create_tables([User, Post, Relationship], safe=True)
    psql_db.close()
