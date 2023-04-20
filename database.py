import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, sessionmaker

from config import mylog, mypass, myserv, myport, mybd

Base = declarative_base()
DSN = f'postgresql://{mylog}:{mypass}@{myserv}:{myport}/{mybd}'
engine = sq.create_engine(DSN)
Session = sessionmaker(bind=engine)
session = Session()


class Viewed(Base):
    __tablename__ = "viewed_profiles"

    id = sq.Column(sq.Integer, primary_key=True)
    user_id = sq.Column(sq.Integer, nullable=False)
    name = sq.Column(sq.Text, nullable=False)


class Best(Base):
    __tablename__ = "best_profiles"

    id = sq.Column(sq.Integer, primary_key=True)
    user_id = sq.Column(sq.Integer, nullable=False)
    name = sq.Column(sq.Text, nullable=False)


def create_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def add_profiles(profiles):
    checking_profiles = []
    for profile in profiles:
        user = session.query(Viewed).filter(Viewed.user_id == profile['id']).all()
        if not user:
            ap = Viewed(user_id=profile['id'], name=profile['name'])
            session.add(ap)
            session.commit()
            checking_profiles.append({'name': profile['name'], 'id': profile['id']})
    return checking_profiles


def add_best_profile(user_id, name):
    user = session.query(Best).filter(Best.user_id == user_id).all()
    if not user:
        ap = Best(user_id=user_id, name=name)
        session.add(ap)
        session.commit()
        text = 'Анкета успешно добавлена в Лучшие.'
    else:
        text = 'Эта анкета уже есть в списке Лучших.'
    return text


def get_best_profiles():
    best_profiles = []
    profiles_tables = session.query(Best).all()
    for profile in profiles_tables:
        best_profiles.append({'name': profile.name, 'id': profile.user_id})
    return best_profiles

