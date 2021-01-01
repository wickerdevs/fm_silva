from fmsilva.bot.commands import *


@send_typing_action
def instagram_log_out(update, context):
    if check_auth(update, context):
        instasession = InstaSession(update.effective_chat.id, update.effective_user.id)
        # User is authorised
        message = send_message(update, context, logging_out)
        if instasession.get_creds():
            instasession.delete_creds()
            text = instagram_loggedout_text
        else:
            text = not_logged_in_logout_text
        instasession.discard()
        markup = CreateMarkup({Callbacks.ACCOUNT: 'Account Info'}).create_markup()
        message.edit_text(text=text, reply_markup=markup)

