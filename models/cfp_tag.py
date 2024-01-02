from main import db
import sqlalchemy
from . import BaseModel


class Tag(BaseModel):
    # A proposal can have multiple tags, which can be filtered on.
    # Tags aren't deleted or modified in normal use, only created.

    __versioned__: dict = {}
    __tablename__ = "tag"

    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String, nullable=False, unique=True)

    proposals = db.relationship(
        "Proposal",
        back_populates="tags",
        secondary="ProposalTag",
    )

    def __init__(self, tag: str):
        self.tag = tag.strip().lower()

    def __str__(self):
        return self.tag

    def __repr__(self):
        return f"<Tag {self.id} '{self.tag}'>"

    @classmethod
    def serialise_tags(self, tag_list: list["Tag"]) -> str:
        return ",".join([str(t) for t in tag_list])

    @classmethod
    def from_mapper(cls, tag_str: str) -> "Tag":
        key = session.identity_key(Tag, tag_str)
        return session.identity_map.get(key, Tag(tag_str))

    @classmethod
    def parse_serialised_tags(cls, tag_str: str) -> list["Tag"]:
        # While parsing, we map any tags that are already in the session.
        # This will be the case if the tags haven't changed. We can then
        # skip trying to reinsert any existing ones.
        tag_list = [t.strip().lower() for t in tag_str.split(",")]
        tag_list = filter(None, tag_list)
        return [Tag.from_mapper(t) for t in tag_list]


ProposalTag: sqlalchemy.Table = db.Table(
    "proposal_tag",
    BaseModel.metadata,
    db.Column(
        "proposal_id", db.Integer, db.ForeignKey("proposal.id"), primary_key=True
    ),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
)
