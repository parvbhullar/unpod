def prepare_post_mail(name, from_user, space_name, title, description, content, link):
    body = f"""
        <!DOCTYPE html>
        <html>
        <body>
            <div class="container">
                <p>Hey, {name}</p>

                <p> <strong>{from_user}</strong> posted new insight on <strong>{space_name}</strong> </p>
                <a href="{ link }">Click Here</a></p>

                <p><strong>Title:</strong><br>
                { title }</p>

                <p><strong>Brief Summary:</strong><br>
                { description}</p>

                <br>

                <p>{ content }</p>

                <p>You can read the full post by clicking the link below:<br>
                <a href="{ link }">Click Here</a></p>

                <p>Thank you for being an active member of our community! Stay tuned for more updates and engaging content.</p>
            </div>
        </body>
        </html>


    """
    return body
