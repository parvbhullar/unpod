from rest_framework import serializers
from unpod.common.string import generate_code, textify


class PostTitleValidation(serializers.Serializer):
    title = serializers.CharField(required=False, max_length=99)

    def validate(self, data):
        data = super(PostTitleValidation, self).validate(data)
        post_type = self.initial_data.get("post_type")
        content_type = self.initial_data.get("content_type")
        content = data.get("content")
        pilot = self.initial_data.get("pilot", "").lower()
        title = data.get("title")
        if not title:
            if post_type in ["notebook"]:
                data["title"] = f"Notebook-Run-{generate_code(6)}"
            elif post_type not in ["ask"] and content_type != "voice":
                raise serializers.ValidationError(
                    {"title": f"Title is required for post type - {post_type}"}
                )
            else:
                if pilot in ["cbird-question-rectifier", "question-reviewer"]:
                    data["title"] = textify(content)
                else:
                    data["title"] = "No Title"
        if data.get("title"):
            data["title"] = data["title"].encode("unicode-escape").decode()
        return data
