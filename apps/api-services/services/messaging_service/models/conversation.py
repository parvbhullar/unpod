from mongomantic import BaseRepository, MongoDBModel, Index
from services.messaging_service.core.mixin import CreateUpdateMixinModel
from services.messaging_service.schemas.conversation import (
    BlockModelSchema,
    BlockReactionSchema,
    CheggQuestionSolverLogs,
)


class BlockBaseModel(BlockModelSchema, MongoDBModel, CreateUpdateMixinModel):
    pass


class BlockModel(BaseRepository):
    class Meta:
        model = BlockBaseModel
        collection = "blocks"
        indexes = [
            Index(fields=["thread_id"]),
            Index(fields=["block_id"]),
            Index(fields=["user_id"]),
            Index(fields=["block_type"]),
            Index(fields=["block"]),
            Index(fields=["is_active"]),
        ]


class BlockReactionBaseModel(BlockReactionSchema, MongoDBModel, CreateUpdateMixinModel):
    pass


class BlockReactionModel(BaseRepository):
    class Meta:
        model = BlockReactionBaseModel
        collection = "block_reactions"
        indexes = [
            Index(fields=["thread_id"]),
            Index(fields=["block_id"]),
            Index(fields=["user_id"]),
            Index(fields=["reaction_type"]),
        ]


class CheggQuestionSolverLogsBaseModel(
    CheggQuestionSolverLogs, MongoDBModel, CreateUpdateMixinModel
):
    pass


class CheggQuestionSolverLogsModel(BaseRepository):
    class Meta:
        model = CheggQuestionSolverLogsBaseModel
        collection = "chegg_question_solver_logs"
        indexes = [
            Index(fields=["thread_id"]),
            Index(fields=["user_id"]),
            Index(fields=["status"]),
        ]
