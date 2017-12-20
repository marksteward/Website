# coding=utf-8

from datetime import datetime

from flask import render_template, current_app as app
from flask_script import Command
from flask_mail import Message
from sqlalchemy import or_, func
from sqlalchemy.orm.exc import NoResultFound

from main import mail, db
from apps.common.receipt import attach_tickets
from models.ticket import Ticket, TicketPrice, TicketType
from models.user import User

def add_ticket_types(types):
    for tt in types:
        try:
            existing_tt = TicketType.query.filter_by(fixed_id=tt.fixed_id).one()

        except NoResultFound:
            app.logger.info('Adding TicketType %s (fixed_id: %s)', tt.name, tt.fixed_id)
            db.session.add(tt)

        else:
            # NB we don't even consider updating prices. If we do, make sure no tickets have been bought.
            app.logger.info('Refreshing TicketType %s (id: %s, fixed_id: %s)', tt.name, existing_tt.id, tt.fixed_id)
            for f in ['name', 'type_limit', 'expires', 'personal_limit', 'order',
                      'has_badge', 'is_transferable', 'description']:
                cur_val = getattr(existing_tt, f)
                new_val = getattr(tt, f)

                if cur_val != new_val:
                    app.logger.info(' %10s: %r -> %r', f, cur_val, new_val)
                    setattr(existing_tt, f, new_val)

        db.session.commit()

    app.logger.info('Tickets refreshed')

def get_main_ticket_types():
    #
    # Update the DB consistently without breaking existing tickets.
    #
    # Ticket prices are immutable, so to change prices, create a new type
    # with a unique id, and set the type limit for the previous one to the
    # number of guaranteed paid tickets (which might be 0).
    #
    # This is fiddly. It should probably be moved out to a json file.

    type_data = [
        # (fixed_id, order, admits, name, type limit, personal limit, GBP, EUR, badge, description, [token, expiry, transferable])
        # Leave order 0 & 1 free for discount tickets
        (12, 1, 'full', 'Full Camp Ticket (Discount Template)', 0, 1, 105.00, 142.00, True, None, 'example', datetime(2016, 8, 1, 12, 0), False),
        (0, 2, 'full', 'Full Camp Ticket', 193, 10, 100.00, 140.00, True, None, None, datetime(2016, 1, 10, 20, 24), True),
        (1, 3, 'full', 'Full Camp Ticket', 350, 10, 110.00, 145.00, True, None, None, datetime(2016, 3, 6, 13, 5), True),
        (2, 4, 'full', 'Full Camp Ticket', 659, 10, 120.00, 158.00, True, None, None, datetime(2016, 7, 24, 0, 0), True),
        (3, 8, 'full', 'Full Camp Ticket (Supporter)', 56, 10, 130.00, 180.00, True,
            "Support this non-profit event by paying a bit more. "
            "All money will go towards making EMF more awesome.",
            None, datetime(2016, 6, 8, 0, 0), True),
        (9, 8, 'full', 'Full Camp Ticket (Supporter)', 140, 10, 130.00, 170.00, True,
            "Support this non-profit event by paying a bit more. "
            "All money will go towards making EMF more awesome.",
            None, datetime(2016, 7, 24, 0, 0), True),

        (4, 9, 'full', 'Full Camp Ticket (Gold Supporter)', 6, 10, 150.00, 210.00, True,
            "Pay even more, receive our undying gratitude.",
            None, datetime(2016, 6, 8, 0, 0), True),
        (10, 9, 'full', 'Full Camp Ticket (Gold Supporter)', 45, 10, 150.00, 195.00, True,
            "Pay even more, receive our undying gratitude.",
            None, datetime(2016, 7, 24, 0, 0), True),

        (5, 10, 'kid', 'Under-16 Camp Ticket', 11, 10, 45.00, 64.00, True,
            "For visitors born after August 5th, 2000. "
            "All under-16s must be accompanied by an adult.",
            None, datetime(2016, 6, 8, 0, 0), True),
        (11, 10, 'kid', 'Under-16 Camp Ticket', 500, 80, 45.00, 60.00, True,
            "For visitors born after August 5th, 2000. "
            "All under-16s must be accompanied by an adult.",
            None, datetime(2016, 8, 4, 0, 0), True),

        (6, 15, 'kid', 'Under-5 Camp Ticket', 35, 4, 0, 0, False,
            "For children born after August 5th, 2011. "
            "All children must be accompanied by an adult.",
            None, datetime(2016, 8, 4, 0, 0), True),

        (13, 25, 'other',
            'Tent (Template)', 0, 1, 300.00, 400.00, False,
            "Pre-ordered village tents will be placed on site before the event starts.",
            'example', datetime(2016, 7, 1, 12, 0), True),

        (14, 30, 'other',
            "Semi-fitted T-Shirt - S", 200, 10, 10.00, 12.00, False,
            "Pre-order the official Electromagnetic Field t-shirt. T-shirts will be available to collect during the event.",
            None, datetime(2016, 7, 15, 0, 0), False),
        (15, 31, 'other', "Semi-fitted T-Shirt - M", 200, 10, 10.00, 12.00, False, None, None, datetime(2016, 7, 15, 0, 0), False),
        (16, 32, 'other', "Semi-fitted T-Shirt - L", 200, 10, 10.00, 12.00, False, None, None, datetime(2016, 7, 15, 0, 0), False),
        (17, 33, 'other', "Semi-fitted T-Shirt - XL", 200, 10, 10.00, 12.00, False, None, None, datetime(2016, 7, 15, 0, 0), False),
        (18, 34, 'other', "Semi-fitted T-Shirt - XXL", 200, 10, 10.00, 12.00, False, None, None, datetime(2016, 7, 15, 0, 0), False),
        (19, 35, 'other', "Unfitted T-Shirt - S", 200, 10, 10.00, 12.00, False, None, None, datetime(2016, 7, 15, 0, 0), False),
        (20, 36, 'other', "Unfitted T-Shirt - M", 200, 10, 10.00, 12.00, False, None, None, datetime(2016, 7, 15, 0, 0), False),
        (21, 37, 'other', "Unfitted T-Shirt - L", 200, 10, 10.00, 12.00, False, None, None, datetime(2016, 7, 15, 0, 0), False),
        (22, 38, 'other', "Unfitted T-Shirt - XL", 200, 10, 10.00, 12.00, False, None, None, datetime(2016, 7, 15, 0, 0), False),
        (23, 39, 'other', "Unfitted T-Shirt - XXL", 200, 10, 10.00, 12.00, False, None, None, datetime(2016, 7, 15, 0, 0), False),

        (7, 50, 'car', 'Parking Ticket', 700, 4, 15.00, 21.00, False,
            "We're trying to keep cars to a minimum. "
            "Please take public transport or car-share if you can.",
            None, None, True),

        (24, 50, 'car', 'Parking Ticket (Cash)', 700, 4, 0, 0, False,
            "We're trying to keep cars to a minimum. "
            "Please take public transport or car-share if you can.",
            None, None, True),

        (8, 55, 'campervan',
            u'Caravan/\u200cCampervan Ticket', 60, 2, 30.00, 42.00, False,
            "If you bring a caravan, you won't need a separate parking ticket for the towing car.",
            None, None, True),
    ]
    # most of these tickets have no tokens or expiry dates
    assert all([len(t) == 13 for t in type_data])

    types = []
    for row in type_data:
        tt = TicketType(*row[1:5], personal_limit=row[5], description=row[9],
            has_badge=row[8], discount_token=row[10], expires=row[11],
            is_transferable=row[12])
        tt.fixed_id = row[0]
        tt.prices = [TicketPrice('GBP', row[6]), TicketPrice('EUR', row[7])]
        types.append(tt)

    return types

def test_main_ticket_types():
    # Test things like non-unique keys
    types = get_main_ticket_types()
    fixed_ids = [tt.fixed_id for tt in types]
    if len(set(fixed_ids)) < len(fixed_ids):
        raise Exception('Duplicate ticket type fixed_id')


class CreateTickets(Command):
    def run(self):
        types = get_main_ticket_types()
        add_ticket_types(types)


class SendTransferReminder(Command):

    def run(self):
        users_to_email = User.query.join(Ticket, TicketType).filter(
            TicketType.admits == 'full',
            Ticket.paid == True,  # noqa
            Ticket.transfer_reminder_sent == False,
        ).group_by(User).having(func.count() > 1)

        for user in users_to_email:
            msg = Message("Your Electromagnetic Field Tickets",
                          sender=app.config['TICKETS_EMAIL'],
                          recipients=[user.email])

            msg.body = render_template("emails/transfer-reminder.txt", user=user)

            app.logger.info('Emailing %s transfer reminder', user.email)
            mail.send(msg)

            for ticket in user.tickets:
                ticket.transfer_reminder_sent = True
            db.session.commit()


class SendTickets(Command):

    def run(self):
        paid_items = Ticket.query.filter_by(paid=True).join(TicketType).filter(or_(
            TicketType.admits.in_(['full', 'kid', 'car', 'campervan']),
            TicketType.fixed_id.in_(range(14, 24))))

        users = (paid_items.filter(Ticket.emailed == False).join(User)  # noqa
                           .group_by(User).with_entities(User).order_by(User.id))

        for user in users:
            user_tickets = Ticket.query.filter_by(paid=True).join(TicketType, User).filter(
                TicketType.admits.in_(['full', 'kid', 'car', 'campervan']),
                User.id == user.id)

            plural = (user_tickets.count() != 1 and 's' or '')

            msg = Message("Your Electromagnetic Field Ticket%s" % plural,
                          sender=app.config['TICKETS_EMAIL'],
                          recipients=[user.email])

            msg.body = render_template("emails/receipt.txt", user=user)

            attach_tickets(msg, user)

            app.logger.info('Emailing %s receipt for %s tickets', user.email, user_tickets.count())
            mail.send(msg)

            db.session.commit()


class CreateParkingTickets(Command):
    def run(self):
        tt = TicketType.query.filter_by(fixed_id=24).one()

        for i in range(1, 50 + 1):
            email = 'user_%s@parking.invalid' % i
            if not User.query.filter_by(email=email).first():
                u = User(email, 'Parking ticket %s' % i)
                db.session.add(u)
                db.session.commit()

                t = Ticket(u.id, tt)
                t.paid = True
                t.emailed = True

        db.session.commit()