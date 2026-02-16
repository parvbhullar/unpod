def get_post_invite_mail_body(invite_link, post_title, invite_by, valid_upto):
    message = f"<p>Dear ,</p>"
    message += f"<p>{invite_by} has requested you to view the thread/post <strong> {post_title} </strong></p>"
    message += f"<p><a href='{invite_link}'>Click here </a> to join the thread/post</p>"
    message += f"<p>This invite link is valid till {valid_upto.strftime('%d-%m-%Y')}</p>"
    message += f"<p>Please copy below link if above link not opening </p>"
    message += f"<p> <strong> {invite_link} </strong> </p>"
    message += "<p>If you are receiving this mail in spam and unable to click on link, please move this email from the Spam folder.</p>"
    # message += f"<br/>"
    message += "<p>Regards<br>"
    message += "<p>Unpod Team</p>"
    return message
