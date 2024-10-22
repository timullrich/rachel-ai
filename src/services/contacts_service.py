# Standard library imports
import os
import logging
import vobject


class ContactsService:
    def __init__(
            self, contacts_file_path: str,
            user_language: str = "en"
    ):
        self.contacts_file_path = contacts_file_path
        self.user_language = user_language

        self.logger = logging.getLogger(self.__class__.__name__)

    def list(self):
        """
        Reads the contacts from the vCard file and returns a list of contacts.

        Returns:
            list: A list of dictionaries, each representing a contact.
        """
        if not os.path.exists(self.contacts_file_path):
            self.logger.error(f"Contacts file not found at {self.contacts_file_path}")
            return []

        try:
            with open(self.contacts_file_path, 'r') as f:
                vcard_data = f.read()

            vcards = vobject.readComponents(vcard_data)
            contacts = []
            for vcard in vcards:
                contact = {
                    'name': vcard.fn.value if hasattr(vcard, 'fn') else 'Unknown',
                    'emails': [email.value for email in getattr(vcard, 'email_list', [])],
                    'phones': [tel.value for tel in getattr(vcard, 'tel_list', [])]
                }
                contacts.append(contact)

            return contacts

        except Exception as e:
            self.logger.error(f"Error reading contacts: {e}")
            return []