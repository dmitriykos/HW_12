from collections import UserDict
from datetime import datetime
import pickle
from pathlib import Path
import re
# _______________________________________________________________
# декоратор


def input_error(func):
    def wrapper(*args, **kwargs):
        try:
            res = func(*args, **kwargs)
            return res
        except KeyError:
            return "This record is not exist"
        except ValueError:
            return "This record is not correct!"
        except IndexError:
            return "This command is wrong"
    return wrapper


# _______________________________________________________________
# classes

class Field:
    def __init__(self, value):
        self._value = value.strip().lower().title()

    def __str__(self):
        return self._value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value.strip().lower().title()


class Name(Field):
    @Field.value.setter
    def value(self, value):
        self._value = value.strip().lower().title()


class Phone(Field):
    @staticmethod
    def valid_phone(phone):
        new_phone = str(phone).strip().removeprefix("+").replace(
            "(", "").replace(")", "").replace("-", "").replace(" ", "")
        try:
            new_phone = [str(int(i)) for i in new_phone]
        except ValueError:
            print("Phone number is not correct. Try again.")

        else:
            new_phone = "".join(new_phone)
            if len(new_phone) == 12:
                return f"+{new_phone}"
            elif len(new_phone) == 10:
                return f"+38{new_phone}"
            else:
                print("Phone number is wrong. Try again")

    def __init__(self, value):
        self._value = Phone.valid_phone(value)

    @Field.value.setter
    def value(self, value):
        self._value = Phone.valid_phone(value)


class Birthday(datetime):
    def valid_date(year, month, day):
        try:
            birthday = datetime(year=year, month=month, day=day)
        except ValueError:
            print("Date is not correct. Enter: YYYY-m-d")
        else:
            return str(birthday.date())

    def __init__(self, year, month, day):
        self.__birthday = self.valid_date(year, month, day)

    @property
    def birthday(self):
        return self.__birthday

    @birthday.setter
    def birthday(self, year, month, day):
        self.__birthday = self.valid_date(year, month, day)


class Record:

    def __init__(self, name: Name, phone: Phone = None, birthday=None):
        self.name = name
        if birthday is not None:
            self.birthday = Birthday(birthday)
        else:
            self.birthday = None

        self.phones = []
        if phone:
            self.phones.append(phone)

    def add_phone(self, phone):
        phone = Phone(phone)
        if phone:
            lst = [phone.value for phone in self.phones]
            if phone.value not in lst:
                self.phones.append(phone)
                return "Phone was added"
        else:
            raise ValueError("Phone number is not correct")

    def change_phone(self, old_phone, new_phone):
        old_phone = Phone(old_phone)
        new_phone = Phone(new_phone)

        for phone in self.phones:
            if phone.value == old_phone.value:
                self.phones.remove(phone)
                self.phones.append(new_phone)
                return "Phone was changed"

    def delete_phone(self, old_phone):
        old_phone = Phone(old_phone)
        for phone in self.phones:
            if phone.value == old_phone.value:
                self.phones.remove(phone)

    def add_birthday(self, year, month, day):
        self.birthday = Birthday.valid_date(int(year), int(month), int(day))

    def days_to_birth_day(self):
        today = datetime.now().date()
        current_year = today.year

        if self.birthday is not None:
            birthday = datetime.strptime(self.birthday, '%Y-%m-%d')
            this_birthday = datetime(current_year, birthday.month,
                                     birthday.day).date()
            delta = this_birthday - today
            if delta.days >= 0:
                return f"{self.name}'s birthday will be in {delta.days} days"
            else:
                next_birthday = datetime(current_year + 1, birthday.month,
                                         birthday.day).date()
                delta = next_birthday - today
                return f"Birthday will be through {delta.days} days"
        else:
            return f"Birthday is unknown"

    def get_contact(self):
        phones = ", ".join([str(p) for p in self.phones])
        return {
            "name": str(self.name.value),
            "phone": phones,
            "birthday": self.birthday
        }


class AddressBook(UserDict):

    def add_record(self, record: Record):
        self.data[record.name.value] = record

    def remove_record(self, name):
        name = name.lower().title()
        if name in self.data:
            self.data.pop(name)

    def all_records(self):
        return {key: value.get_contact() for key, value in self.data.items()}

    def iterator(self):
        for record in self.data.values():
            yield record.get_contact()


path = Path("add_book.bin")
contacts = AddressBook()
if path.exists():
    with open("add_book.bin", "rb") as fh:
        contacts.data = pickle.load(fh)


# ______________________________________________________________
# Bot


def save_to_file():
    with open("add_book.bin", "wb") as fh:
        pickle.dump(contacts.data, fh)


@input_error
def search(value: str):
    for record in contacts:
        contact = contacts[record]
        for text in contact.get_contact().values():
            if text != None:
                if re.findall(value, text):
                    print(contacts[record].get_contact())
                    break


def greeting(*args):
    return "How can I help you?"


@input_error
def add_contact(value):
    name, *phones = value.lower().strip().split()
    name = Name(name.lower().title())

    if not name.value in contacts:
        record = Record(name)
        contacts.add_record(record)
        for phone in phones:
            record.add_phone(phone)
            save_to_file()
        return f"Contact added"
    else:
        return f"Contact already exists"


@input_error
def add_phone(value):
    name, phone = value.lower().strip().split()
    if name.title() in contacts:
        contacts[name.title()].add_phone(phone)
        save_to_file()
        return f"Phone was recorded"
    else:
        return f"Contact is absent"


@input_error
def remove_phone(value):
    name, phone = value.lower().strip().split()

    if name.title() in contacts:
        contacts[name.title()].delete_phone(phone)
        save_to_file()
        return f"Phone was delete"
    else:
        return f"Contact is absent"


@input_error
def contact_birthday(value):
    name, birthday = value.lower().strip().split()
    birthday = tuple(birthday.split("-"))

    if name.title() in contacts:
        contacts[name.title()].add_birthday(*birthday)
        save_to_file()
        return f"Birthday was recorded"
    else:
        return f"Contact is absent"


@input_error
def days_to_birthday(name):
    if name.title() in contacts:
        if not contacts[name.title()].birthday is None:
            days = contacts[name.title()].days_to_birth_day()
            return days
        else:
            return f"Birthday is unknown"
    else:
        return f"Contact is absent"


@input_error
def change_ph(value: str):
    name, old_phone, new_phone = value.split()

    if name.strip().lower().title() in contacts:
        contacts[name.strip().lower().title()].change_phone(
            old_phone, new_phone)
        save_to_file()
    else:
        return f"Contact is absent"


@input_error
def remove_contact(name: str):
    record = contacts[name.strip().lower().title()]
    contacts.remove_record(record.name.value)
    save_to_file()
    return f"Contact removed"


@input_error
def phone(name):
    if name.title() in contacts:
        record = contacts[name.title()]
        return record.get_contact()
    else:
        return f"Contact is absent"


def show_all(s):
    if len(contacts) == 0:
        return "Phone book is empty"
    for record in contacts.values():
        print(record.get_contact())


COMMANDS = {
    "hello": greeting,
    "add": add_contact,
    "phone": phone,
    "remove contact": remove_contact,
    "add phone": add_phone,
    "change phone": change_ph,
    "remove phone": remove_phone,
    "add birthday": contact_birthday,
    "days to birthday": days_to_birthday,
    "search": search,
    "show all": show_all
}


@input_error
def main():
    while True:
        user = input(">>> ")
        user_input = user.casefold()

        if user_input == ".":
            break
        if user_input.startswith(('good bye', 'exit', 'close')):
            print("Good bay!")
            break

        for key in COMMANDS:
            if user_input.lower().strip().startswith(key):
                print(COMMANDS[key](user_input[len(key):].strip()))
                break


if __name__ == "__main__":
    main()
    save_to_file()
