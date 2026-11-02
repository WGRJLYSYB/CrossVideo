# CrossVideo — Cross-platform video playback progress synchronization tool
# Copyright (C) 2026 WGRJLYSYB
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import argparse
import getpass
import re
import sys

from sqlalchemy import select

from .auth import hash_password
from .db import SessionLocal
from .models import User


def _read_password(prompt: str = "Password: ") -> str:
    password = getpass.getpass(prompt)
    if len(password) < 8 or len(password) > 128:
        raise ValueError("password must be 8-128 characters")
    if not any(character.isalpha() for character in password) or not any(character.isdigit() for character in password):
        raise ValueError("password must contain both letters and numbers")
    return password


def create_superuser(username: str) -> None:
    if not 3 <= len(username) <= 50 or re.search(r"\s", username):
        raise ValueError("username must be 3-50 characters with no whitespace")
    password = _read_password()
    confirmation = _read_password("Confirm password: ")
    if password != confirmation:
        raise ValueError("passwords do not match")
    with SessionLocal() as db:
        if db.scalar(select(User.id).where(User.username == username)) is not None:
            raise ValueError(f"user {username!r} already exists")
        db.add(User(username=username, hashed_password=hash_password(password), is_superuser=True))
        db.commit()
    print(f"Superuser {username!r} created.")


def set_password(username: str) -> None:
    password = _read_password()
    confirmation = _read_password("Confirm password: ")
    if password != confirmation:
        raise ValueError("passwords do not match")
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == username))
        if user is None:
            raise ValueError(f"user {username!r} does not exist")
        user.hashed_password = hash_password(password)
        db.commit()
    print(f"Password updated for {username!r}.")


def list_superusers() -> None:
    with SessionLocal() as db:
        users = db.scalars(
            select(User).where(User.is_superuser.is_(True)).order_by(User.username)
        ).all()
        if not users:
            print("No superusers.")
            return
        print("ID\tUsername\tState\tCreated At")
        for user in users:
            state = "active" if user.is_active else "disabled"
            print(f"{user.id}\t{user.username}\t{state}\t{user.created_at}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="crossvideo", description="CrossVideo account administration")
    commands = parser.add_subparsers(dest="command", required=True)

    create_parser = commands.add_parser("create-superuser", help="create a superuser without public registration")
    create_parser.add_argument("username")
    password_parser = commands.add_parser("set-password", help="set a user's password")
    password_parser.add_argument("username")
    commands.add_parser("list-superusers", help="list superuser accounts")
    args = parser.parse_args()

    try:
        if args.command == "create-superuser":
            create_superuser(args.username)
        elif args.command == "set-password":
            set_password(args.username)
        else:
            list_superusers()
    except (ValueError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
