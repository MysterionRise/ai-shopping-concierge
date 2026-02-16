from app.models.base import Base, TimestampMixin
from app.models.conversation import Conversation, Message
from app.models.product import Product
from app.models.user import User


def test_user_model_tablename():
    assert User.__tablename__ == "users"


def test_product_model_tablename():
    assert Product.__tablename__ == "products"


def test_conversation_model_tablename():
    assert Conversation.__tablename__ == "conversations"


def test_message_model_tablename():
    assert Message.__tablename__ == "messages"


def test_base_is_declarative():
    assert hasattr(Base, "metadata")


def test_timestamp_mixin_has_fields():
    assert hasattr(TimestampMixin, "id")
    assert hasattr(TimestampMixin, "created_at")
    assert hasattr(TimestampMixin, "updated_at")
