from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    picks = relationship("Pick", back_populates="player", cascade="all, delete-orphan")

class Pick(Base):
    __tablename__ = "picks"
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"))
    team = Column(String, nullable=False)
    player = relationship("Player", back_populates="picks")

class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True)
    round = Column(String, nullable=False)          # group / R32 / R16 / QF / SF / 3rd / Final
    grp = Column(String, nullable=True)             # group letter for group games
    team_a = Column(String, nullable=True)
    team_b = Column(String, nullable=True)
    score_a = Column(Integer, nullable=True)
    score_b = Column(Integer, nullable=True)
    winner = Column(String, nullable=True)          # for shootouts / explicit
    status = Column(String, default="SCHEDULED")    # SCHEDULED / LIVE / FINISHED
    kickoff = Column(DateTime, nullable=True)
    ext_id = Column(String, nullable=True)          # football-data match id
    network = Column(String, nullable=True)         # TV network(s), e.g. "FOX · Telemundo"
    slot_a = Column(String, nullable=True)          # ESPN placeholder when team unknown, e.g. "1F", "3RD B/E/F/I/J"
    slot_b = Column(String, nullable=True)
    manual = Column(Boolean, default=False)         # if True, API sync won't overwrite
