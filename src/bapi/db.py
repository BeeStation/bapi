from bapi import ma_ext
from bapi import sqlalchemy_ext
from sqlalchemy import and_
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import SmallInteger
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm.exc import NoResultFound

db_session = sqlalchemy_ext.session


class Player(sqlalchemy_ext.Model):
    __bind_key__ = "game"
    __tablename__ = "SS13_player"

    ckey = Column("ckey", String(32), primary_key=True)
    byond_key = Column("byond_key", String(32))
    firstseen = Column("firstseen", DateTime())
    firstseen_round_id = Column("firstseen_round_id", Integer())
    lastseen = Column("lastseen", DateTime())
    lastseen_round_id = Column("lastseen_round_id", Integer())
    ip = Column("ip", Integer())
    computerid = Column("computerid", String(32))
    uuid = Column("uuid", String(64))
    lastadminrank = Column("lastadminrank", String(32))
    accountjoindate = Column("accountjoindate", Date())
    flags = Column("flags", SmallInteger())
    antag_tokens = Column("antag_tokens", SmallInteger())
    metacoins = Column("metacoins", Integer())

    @classmethod
    def from_ckey(cls, ckey):
        try:
            return db_session.query(cls).filter(cls.ckey == ckey).one()
        except NoResultFound:
            return None

    def get_connection_count(self):
        return db_session.query(Connection).filter(Connection.ckey == self.ckey).count()

    def get_death_count(self):
        return db_session.query(Death).filter(Death.byondkey == self.ckey).count()

    def get_round_count(self):
        # We have to only query the round_id so the distinct thing will work because haha sqlalchemy
        return (
            db_session.query(Connection.round_id)
            .filter(Connection.ckey == self.ckey)
            .distinct(Connection.round_id)
            .count()
        )

    def get_bans(self):
        return query_grouped_bans().filter(Ban.ckey == self.ckey).order_by(Ban.bantime.desc()).all()

    def get_role_time(self, role):
        try:
            time_for_role = (
                db_session.query(RoleTime).filter(and_(RoleTime.ckey == self.ckey, RoleTime.job == role)).one()
            )

            return time_for_role.minutes

        except NoResultFound:
            return 0

    def get_total_playtime(self):
        living_time = self.get_role_time("Living")
        ghost_time = self.get_role_time("Ghost")

        return living_time + ghost_time

    def get_favorite_job(self):
        try:
            most_played_role = (
                db_session.query(RoleTime)
                .filter(
                    and_(
                        RoleTime.ckey == self.ckey,
                        RoleTime.job != "Living",  # probably not the best way to do this but.... UGHHH
                        RoleTime.job != "Ghost",
                        RoleTime.job != "Admin",
                        RoleTime.job != "Mentor",
                    )
                )
                .order_by(RoleTime.minutes.desc())
                .first()
            )

            return most_played_role

        except NoResultFound:
            return None


class Round(sqlalchemy_ext.Model):
    __bind_key__ = "game"
    __tablename__ = "SS13_round"

    id = Column("id", Integer(), primary_key=True)
    initialize_datetime = Column("initialize_datetime", DateTime())
    start_datetime = Column("start_datetime", DateTime())
    shutdown_datetime = Column("shutdown_datetime", DateTime())
    end_datetime = Column("end_datetime", DateTime())
    server_name = Column("server_name", String(32))
    server_ip = Column("server_ip", Integer())
    server_port = Column("server_port", SmallInteger())
    commit_hash = Column("commit_hash", String(40))
    game_mode = Column("game_mode", String(32))
    game_mode_result = Column("game_mode_result", String(64))
    end_state = Column("end_state", String(64))
    shuttle_name = Column("shuttle_name", String(64))
    map_name = Column("map_name", String(32))
    station_name = Column("station_name", String(80))

    @classmethod
    def from_id(cls, id):
        try:
            return db_session.query(cls).filter(cls.id == id).one()
        except NoResultFound:
            return None

    @classmethod
    def get_latest(cls):
        return db_session.query(cls).order_by(cls.id.desc()).first()

    def in_progress(self):
        if self.shutdown_datetime:
            return False

        return True


class Death(sqlalchemy_ext.Model):
    __bind_key__ = "game"
    __tablename__ = "SS13_death"

    id = Column("id", Integer(), primary_key=True)
    tod = Column("tod", DateTime())
    server_ip = Column("server_ip", Integer())
    server_port = Column("server_port", SmallInteger())
    round_id = Column("round_id", Integer())
    byondkey = Column("byondkey", String(32))
    suicide = Column("suicide", SmallInteger())


class Connection(sqlalchemy_ext.Model):
    __bind_key__ = "game"
    __tablename__ = "SS13_connection_log"

    id = Column("id", Integer(), primary_key=True)
    datetime = Column("datetime", DateTime())
    server_name = Column("server_name", String(32))
    server_ip = Column("server_ip", Integer())
    server_port = Column("server_port", SmallInteger())
    round_id = Column("round_id", Integer())
    ckey = Column("ckey", String(32))
    ip = Column("ip", Integer())
    computerid = Column("computerid", String(45))


class Book(sqlalchemy_ext.Model):
    __bind_key__ = "game"
    __tablename__ = "SS13_library"

    id = Column("id", Integer(), primary_key=True)
    author = Column("author", String(32))
    title = Column("title", String(45))
    content = Column("content", String(16777215))
    category = Column(
        "category",
        Enum("Any", "Fiction", "Non-Fiction", "Adult", "Reference", "Religion"),
    )
    ckey = Column("ckey", String(32))
    datetime = Column("datetime", DateTime())
    deleted = Column("deleted", SmallInteger())
    round_id_created = Column("round_id_created", Integer())

    @classmethod
    def from_id(cls, id):
        try:
            return db_session.query(cls).filter(cls.id == id, cls.deleted is None).one()
        except NoResultFound:
            return None


class BookSchema(ma_ext.SQLAlchemyAutoSchema):
    class Meta:
        model = Book


class Ban(sqlalchemy_ext.Model):
    __bind_key__ = "game"
    __tablename__ = "SS13_ban"

    id = Column("id", Integer(), primary_key=True)
    bantime = Column("bantime", DateTime())
    server_name = Column("server_name", String(32))
    server_ip = Column("server_ip", Integer())
    server_port = Column("server_port", SmallInteger())
    round_id = Column("round_id", Integer())
    role = Column("role", String(32))
    expiration_time = Column("expiration_time", DateTime())
    applies_to_admins = Column("applies_to_admins", SmallInteger())
    reason = Column("reason", String(2048))
    ckey = Column("ckey", String(32))
    ip = Column("ip", Integer())
    computerid = Column("computerid", String(32))
    a_ckey = Column("a_ckey", String(32))
    a_ip = Column("a_ip", Integer())
    a_computerid = Column("a_computerid", Integer())
    who = Column("who", String(2048))
    adminwho = Column("adminwho", String(2048))
    edits = Column("edits", Text())
    unbanned_datetime = Column("unbanned_datetime", DateTime())
    unbanned_ckey = Column("unbanned_ckey", String(32))
    unbanned_ip = Column("unbanned_ip", Integer())
    unbanned_computerid = Column("unbanned_computerid", String(32))
    unbanned_round_id = Column("unbanned_round_id", Integer())
    global_ban = Column("global_ban", SmallInteger())
    hidden = Column("hidden", SmallInteger())

    @classmethod
    def from_id(cls, id):
        try:
            return db_session.query(cls).filter(cls.id == id).one()
        except NoResultFound:
            return None

    @classmethod
    def grouped_from_id(
        cls, id
    ):  # For getting job bans with the roles grouped as a separate field, yep it's a headache
        try:
            single_from_id = cls.from_id(id)

            return (
                db_session.query(*([c for c in cls.__table__.c] + [func.group_concat(Ban.role).label("roles")]))
                .group_by(cls.bantime, cls.ckey)
                .filter(
                    cls.ckey == single_from_id.ckey,
                    cls.bantime == single_from_id.bantime,
                )
                .one()
            )

        except NoResultFound:
            return None

    @classmethod  # because stupid grouped bans aren't actually ban classes and are a special row class
    def to_public_dict(cls, ban):
        return {
            "id": ban.id,
            "bantime": ban.bantime,
            "server_name": ban.server_name,
            "round_id": ban.round_id,
            "roles": ban.roles.split(",") if hasattr(ban, "roles") else ban.role,  # grouped ban bs
            "expiration_time": ban.expiration_time if ban.expiration_time else None,
            "reason": ban.reason,
            "ckey": ban.ckey,
            "a_ckey": ban.a_ckey,
            "unbanned_datetime": ban.unbanned_datetime if ban.unbanned_datetime else None,
            "unbanned_ckey": ban.unbanned_ckey,
            "global_ban": ban.global_ban,
        }


def query_grouped_bans(order_by=Ban.id.desc(), search_query=None):
    query = db_session.query(
        *([c for c in Ban.__table__.c] + [func.group_concat(Ban.role).label("roles")])
    )  # All columns from ban + the grouped by role

    query = query.group_by(Ban.bantime, Ban.ckey)

    query = query.filter(Ban.hidden == 0)

    if order_by is not None:
        query = query.order_by(order_by)
    if search_query:
        query = query.filter(Ban.ckey.like(search_query))

    return query


class RoleTime(sqlalchemy_ext.Model):
    __bind_key__ = "game"
    __tablename__ = "SS13_role_time"

    ckey = Column("ckey", String(32), primary_key=True)
    job = Column("job", String(128), primary_key=True)
    minutes = Column("minutes", Integer())


### SITE DB
class Patreon(sqlalchemy_ext.Model):
    __bind_key__ = "site"
    __tablename__ = "patreon_link"

    ckey = Column("ckey", String(32))
    patreon_id = Column("patreon_id", String(32), primary_key=True)

    @classmethod
    def from_ckey(cls, ckey):
        try:
            return db_session.query(cls).filter(cls.ckey == ckey).one()
        except NoResultFound:
            return None

    @classmethod
    def from_patreon_id(cls, patreon_id):
        try:
            return db_session.query(cls).filter(cls.patreon_id == patreon_id).one()
        except NoResultFound:
            return None

    @classmethod
    def link(cls, ckey, patreon_id):
        existing_link = cls.from_patreon_id(patreon_id)

        if existing_link:
            existing_link.ckey = ckey
        else:
            entry = cls(ckey=ckey, patreon_id=patreon_id)
            db_session.add(entry)

        db_session.commit()
