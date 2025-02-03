"""
Applicazione di demo per una piattaforma di streaming 
Utilizza PyQt5 per l'interfaccia e mysql-connector per il database.
"""

import sys
from datetime import date, datetime
import os
import mysql.connector
from mysql.connector import errorcode

from PyQt5.QtCore import QDate, Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QScrollArea,
                             QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QComboBox, QDateEdit, QMessageBox,
                             QTextEdit, QDialog, QFormLayout, QGridLayout, QStackedWidget)
class DatabaseManager:
    def __init__(self, host, user, password, database):
        self.config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database
        }
        try:
            self.conn = mysql.connector.connect(**self.config)
            self.conn.autocommit = True
            self.cursor = self.conn.cursor(dictionary=True)
        except mysql.connector.Error as err:
            print("Errore di connessione:", err)
            sys.exit(1)

    def userExists(self, username):
        query = "SELECT COUNT(*) as cnt FROM Utente WHERE Username = %s;"
        self.cursor.execute(query, (username,))
        result = self.cursor.fetchone()
        return result['cnt'] > 0

    def registerUser(self, username, nome, cognome, dataNascita, citta, indirizzo):
        if self.userExists(username):
            return False, "Username già esistente!"
        query = ("INSERT INTO Utente (Username, Nome, Cognome, DataNascita, Citta, Indirizzo) "
                 "VALUES (%s, %s, %s, %s, %s, %s);")
        try:
            self.cursor.execute(query, (username, nome, cognome, dataNascita, citta, indirizzo))
            self.conn.commit()
            return True, "Registrazione avvenuta con successo."
        except mysql.connector.Error as err:
            return False, f"Errore nella registrazione: {err}"

    def getVideos(self):
        query = "SELECT * FROM VistaVideoPremi;"
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def getVideoByTitle(self, titolo):
        query = "SELECT * FROM Video WHERE Titolo = %s;"
        self.cursor.execute(query, (titolo,))
        return self.cursor.fetchone()

    def getPaymentMethods(self, username):
        query = "SELECT * FROM MetodoDiPagamento WHERE Username = %s;"
        self.cursor.execute(query, (username,))
        return self.cursor.fetchall()

    def insertVisione(self, username, titoloVideo, idMetodo, dataVisione):
        try:
            self.cursor.callproc('SpuInserisciVisione', [username, titoloVideo, idMetodo, dataVisione])
            self.conn.commit()
            return True, "Visione inserita correttamente."
        except mysql.connector.Error as err:
            return False, f"Errore nell'inserimento della visione: {err}"

    def updateWallet(self, metodo_id, new_amount):
        query = "UPDATE MetodoDiPagamento SET Ammontare = %s WHERE ID = %s;"
        try:
            self.cursor.execute(query, (new_amount, metodo_id))
            self.conn.commit()
            return True
        except mysql.connector.Error as err:
            print("Errore nell'aggiornamento del portafoglio:", err)
            return False

    def getMethodByID(self, metodo_id):
        query = "SELECT * FROM MetodoDiPagamento WHERE ID = %s;"
        self.cursor.execute(query, (metodo_id,))
        return self.cursor.fetchone()

    def addPaymentMethod(self, username, tipo, nomeCarta=None, numeroCarta=None, ammontare=None):
        try:
            if tipo == "Carta":
                query = "INSERT INTO MetodoDiPagamento (Tipo, NomeCarta, NumeroCarta, Username) VALUES (%s, %s, %s, %s);"
                params = (tipo, nomeCarta, numeroCarta, username)
            elif tipo == "Portafoglio":
                query = "INSERT INTO MetodoDiPagamento (Tipo, Ammontare, Username) VALUES (%s, %s, %s);"
                params = (tipo, ammontare, username)
            else:
                return False, "Tipo di metodo di pagamento non supportato."
            self.cursor.execute(query, params)
            self.conn.commit()
            return True, "Metodo di pagamento aggiunto con successo."
        except mysql.connector.Error as err:
            return False, f"Errore nell'aggiunta del metodo di pagamento: {err}"

    def getCompanies(self):
        query = "SELECT * FROM Azienda;"
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def getAwards(self):
        query = "SELECT * FROM Premio;"
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def populateMockData(self):
        """Inserisce alcuni dati di esempio se le tabelle risultano vuote."""
        self.cursor.execute("SELECT COUNT(*) as count FROM Video;")
        result = self.cursor.fetchone()
        if result['count'] == 0:
            try:
                self.cursor.execute("INSERT IGNORE INTO Citta (Nome, Nazione) VALUES ('Milano', 'Italia');")
                self.cursor.execute("INSERT IGNORE INTO Citta (Nome, Nazione) VALUES ('Roma', 'Italia');")
                self.cursor.execute("INSERT IGNORE INTO Azienda (Nome, TipoAzienda, NumeroDipendenti, Citta) VALUES ('AziendaProd', 'Produttore', 100, 'Milano');")
                self.cursor.execute("INSERT IGNORE INTO Azienda (Nome, TipoAzienda, NumeroDipendenti, Citta) VALUES ('AziendaDist', 'Distributore', 80, 'Roma');")
                self.cursor.execute("INSERT IGNORE INTO Azienda (Nome, TipoAzienda, NumeroDipendenti, Citta) VALUES ('AziendaMix', 'Entrambi', 150, 'Milano');")
                self.cursor.execute("INSERT IGNORE INTO Utente (Username, Nome, Cognome, DataNascita, Citta, Indirizzo) VALUES ('user1', 'Mario', 'Rossi', '1985-06-15', 'Milano', 'Via Roma 1');")
                self.cursor.execute("INSERT IGNORE INTO Utente (Username, Nome, Cognome, DataNascita, Citta, Indirizzo) VALUES ('user2', 'Luigi', 'Verdi', '1990-03-22', 'Roma', 'Via Milano 2');")
                self.cursor.execute("INSERT IGNORE INTO Video (Titolo, Prezzo, DataUscita, NumeroVisualizzazioni, Produttore, Distributore) VALUES ('Film A', 4.99, '2020-01-01', 0, 'AziendaProd', 'AziendaDist');")
                self.cursor.execute("INSERT IGNORE INTO Video (Titolo, Prezzo, DataUscita, NumeroVisualizzazioni, Produttore, Distributore) VALUES ('Serie B', 2.99, '2019-05-10', 0, 'AziendaMix', 'AziendaDist');")
                self.cursor.execute("INSERT IGNORE INTO MetodoDiPagamento (Tipo, NomeCarta, NumeroCarta, Username) VALUES ('Carta', 'Visa', '1234567890123456', 'user1');")
                self.cursor.execute("INSERT IGNORE INTO MetodoDiPagamento (Tipo, Ammontare, Username) VALUES ('Portafoglio', 50.00, 'user2');")
                self.cursor.execute("INSERT IGNORE INTO Ente (Nome, Tipo, NumeroDiFan) VALUES ('PremioTop', 'Festival', 5000);")
                self.cursor.execute("INSERT IGNORE INTO Premio (Nome, Categoria, Anno, TitoloVideo, Ente) VALUES ('Miglior Film', 'Cinema', 2020, 'Film A', 'PremioTop');")
                self.conn.commit()
            except mysql.connector.Error as err:
                print("Errore nell'inserimento dei dati mock:", err)
class LoginPage(QWidget):
    def __init__(self, dbManager, onLoginSuccess, onRegister):
        super().__init__()
        self.dbManager = dbManager
        self.onLoginSuccess = onLoginSuccess
        self.onRegister = onRegister
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        title = QLabel("Benvenuto nella Piattaforma di Streaming")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title)

        self.usernameEdit = QLineEdit()
        self.usernameEdit.setPlaceholderText("Inserisci il tuo username")
        layout.addWidget(QLabel("Username:"))
        layout.addWidget(self.usernameEdit)

        loginButton = QPushButton("Login")
        loginButton.clicked.connect(self.login)
        layout.addWidget(loginButton)

        registerButton = QPushButton("Registrati")
        registerButton.clicked.connect(self.onRegister)
        layout.addWidget(registerButton)

        self.setLayout(layout)

    def login(self):
        username = self.usernameEdit.text().strip()
        if not username:
            QMessageBox.warning(self, "Errore", "Inserisci un username!")
            return
        if self.dbManager.userExists(username):
            self.onLoginSuccess(username)
        else:
            QMessageBox.critical(self, "Errore", f"Username '{username}' non trovato!")
class RegistrationPage(QWidget):
    def __init__(self, dbManager, onRegistrationSuccess, onBackToLogin):
        super().__init__()
        self.dbManager = dbManager
        self.onRegistrationSuccess = onRegistrationSuccess
        self.onBackToLogin = onBackToLogin
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        title = QLabel("Registrazione Nuovo Utente")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title)

        self.usernameEdit = QLineEdit()
        self.usernameEdit.setPlaceholderText("Username")
        self.nomeEdit = QLineEdit()
        self.nomeEdit.setPlaceholderText("Nome")
        self.cognomeEdit = QLineEdit()
        self.cognomeEdit.setPlaceholderText("Cognome")
        self.dataNascitaEdit = QDateEdit()
        self.dataNascitaEdit.setCalendarPopup(True)
        self.dataNascitaEdit.setDate(QDate(1900, 1, 1))
        self.dataNascitaEdit.setSpecialValueText("Seleziona data")
        self.cittaEdit = QLineEdit()
        self.cittaEdit.setPlaceholderText("Città")
        self.indirizzoEdit = QLineEdit()
        self.indirizzoEdit.setPlaceholderText("Indirizzo")

        formLayout = QFormLayout()
        formLayout.addRow("Username:", self.usernameEdit)
        formLayout.addRow("Nome:", self.nomeEdit)
        formLayout.addRow("Cognome:", self.cognomeEdit)
        formLayout.addRow("Data di Nascita:", self.dataNascitaEdit)
        formLayout.addRow("Città:", self.cittaEdit)
        formLayout.addRow("Indirizzo:", self.indirizzoEdit)
        layout.addLayout(formLayout)

        self.registerButton = QPushButton("Registrati")
        self.registerButton.clicked.connect(self.register)
        layout.addWidget(self.registerButton)

        self.backButton = QPushButton("Torna al Login")
        self.backButton.clicked.connect(self.onBackToLogin)
        layout.addWidget(self.backButton)

        self.setLayout(layout)

    def register(self):
        username = self.usernameEdit.text().strip()
        nome = self.nomeEdit.text().strip()
        cognome = self.cognomeEdit.text().strip()
        if self.dataNascitaEdit.date() == QDate(1900, 1, 1):
            QMessageBox.warning(self, "Errore", "Seleziona la data di nascita!")
            return
        dataNascita = self.dataNascitaEdit.date().toString("yyyy-MM-dd")
        citta = self.cittaEdit.text().strip()
        indirizzo = self.indirizzoEdit.text().strip()
        if not username or not nome or not cognome or not citta or not indirizzo:
            QMessageBox.warning(self, "Errore", "Tutti i campi sono obbligatori!")
            return
        success, msg = self.dbManager.registerUser(username, nome, cognome, dataNascita, citta, indirizzo)
        if success:
            QMessageBox.information(self, "Successo", msg)
            self.onRegistrationSuccess(username)
        else:
            QMessageBox.critical(self, "Errore", msg)
class VideoCard(QWidget):
    clicked = pyqtSignal(str)  # Emette il titolo del video

    def __init__(self, video_data, parent=None):
        super().__init__(parent)
        self.video_data = video_data
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.coverLabel = QLabel()
        if os.path.exists("cover_placeholder.png"):
            pixmap = QPixmap("cover_placeholder.png")
        else:
            pixmap = QPixmap(200, 120)
            pixmap.fill(QColor("#cccccc"))
            painter = QPainter(pixmap)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#ffffff"))
            points = [
                pixmap.rect().center() + QPoint(-10, -15),
                pixmap.rect().center() + QPoint(-10, 15),
                pixmap.rect().center() + QPoint(15, 0)
            ]
            painter.drawPolygon(*points)
            painter.end()
        self.coverLabel.setPixmap(pixmap.scaled(200, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(self.coverLabel)

        titleLabel = QLabel(self.video_data["Titolo"])
        titleLabel.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(titleLabel)

        priceLabel = QLabel(f"€{self.video_data['Prezzo']:.2f}")
        layout.addWidget(priceLabel)

        self.setLayout(layout)
        self.setStyleSheet("""
            VideoCard {
                border: 1px solid #dddddd;
                border-radius: 8px;
                background-color: #ffffff;
            }
            QLabel { color: #333333; }
        """)

    def mousePressEvent(self, event):
        self.clicked.emit(self.video_data["Titolo"])
class CatalogoTab(QWidget):
    def __init__(self, dbManager, loggedUser):
        super().__init__()
        self.dbManager = dbManager
        self.loggedUser = loggedUser
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        header = QLabel("Catalogo Video")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(header)

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.cardsContainer = QWidget()
        self.gridLayout = QGridLayout()
        self.gridLayout.setSpacing(15)
        self.cardsContainer.setLayout(self.gridLayout)
        self.scrollArea.setWidget(self.cardsContainer)
        layout.addWidget(self.scrollArea)

        self.setLayout(layout)
        self.loadData()

    def loadData(self):
        for i in reversed(range(self.gridLayout.count())):
            widgetToRemove = self.gridLayout.itemAt(i).widget()
            self.gridLayout.removeWidget(widgetToRemove)
            widgetToRemove.setParent(None)
        videos = self.dbManager.getVideos()
        columns = 3
        row = 0
        col = 0
        for video in videos:
            card = VideoCard(video)
            card.clicked.connect(self.showVideoDetail)
            self.gridLayout.addWidget(card, row, col)
            col += 1
            if col >= columns:
                col = 0
                row += 1

    def showVideoDetail(self, videoTitle):
        dialog = VideoDetailDialog(self.dbManager, self.loggedUser, videoTitle)
        dialog.exec_()
        self.loadData()
class VideoDetailDialog(QDialog):
    def __init__(self, dbManager, loggedUser, videoTitle):
        super().__init__()
        self.dbManager = dbManager
        self.loggedUser = loggedUser
        self.videoTitle = videoTitle
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Dettagli Video - " + self.videoTitle)
        layout = QFormLayout()
        video = self.dbManager.getVideoByTitle(self.videoTitle)
        if video is None:
            QMessageBox.critical(self, "Errore", "Video non trovato!")
            self.reject()
            return

        layout.addRow("Titolo:", QLabel(video["Titolo"]))
        layout.addRow("Prezzo:", QLabel(f"€{video['Prezzo']:.2f}"))
        layout.addRow("Produttore:", QLabel(video["Produttore"]))
        layout.addRow("Distributore:", QLabel(video["Distributore"]))

        self.paymentCombo = QComboBox()
        methods = self.dbManager.getPaymentMethods(self.loggedUser)
        for m in methods:
            if m["Tipo"] == "Portafoglio":
                display = f"ID:{m['ID']} - {m['Tipo']} (Credito: {m.get('Ammontare', 0)})"
            else:
                display = f"ID:{m['ID']} - {m['Tipo']}"
            self.paymentCombo.addItem(display, m["ID"])
        layout.addRow("Metodo di Pagamento:", self.paymentCombo)

        self.payButton = QPushButton("Paga e Guarda")
        self.payButton.clicked.connect(self.processPayment)
        layout.addRow(self.payButton)

        self.setLayout(layout)

    def processPayment(self):
        metodo_id = self.paymentCombo.currentData()
        method = self.dbManager.getMethodByID(metodo_id)
        video = self.dbManager.getVideoByTitle(self.videoTitle)
        price = video["Prezzo"]

        if method["Tipo"] == "Portafoglio":
            current_credit = method.get("Ammontare", 0)
            if current_credit is None or current_credit < price:
                QMessageBox.warning(self, "Errore", "Credito insufficiente per visualizzare questo video!")
                return
            new_credit = current_credit - price
            if not self.dbManager.updateWallet(metodo_id, new_credit):
                QMessageBox.critical(self, "Errore", "Impossibile aggiornare il credito!")
                return
        dataVisione = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        success, msg = self.dbManager.insertVisione(self.loggedUser, self.videoTitle, metodo_id, dataVisione)
        if success:
            self.accept()
            playerDialog = VideoPlayerPage(self.dbManager, self.loggedUser, self.videoTitle)
            playerDialog.exec_()
        else:
            QMessageBox.critical(self, "Errore", msg)
class VideoPlayerPage(QDialog):
    def __init__(self, dbManager, loggedUser, videoTitle, parent=None):
        super().__init__(parent)
        self.dbManager = dbManager
        self.loggedUser = loggedUser
        self.videoTitle = videoTitle
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Riproduzione Video - " + self.videoTitle)
        layout = QVBoxLayout()
        headerLayout = QHBoxLayout()
        backButton = QPushButton("Torna al Catalogo")
        backButton.clicked.connect(self.accept)
        headerLayout.addWidget(backButton)
        headerLayout.addStretch()
        layout.addLayout(headerLayout)
        playerArea = QLabel("Riproduzione streaming in corso...")
        playerArea.setFixedSize(600, 400)
        playerArea.setAlignment(Qt.AlignCenter)
        playerArea.setStyleSheet("border: 2px solid #0078d7; background-color: #000000; color: #ffffff;")
        layout.addWidget(playerArea, alignment=Qt.AlignCenter)
        video = self.dbManager.getVideoByTitle(self.videoTitle)
        views = video.get("NumeroVisualizzazioni", 0) if video else 0
        viewsLabel = QLabel(f"Visualizzazioni: {views}")
        viewsLabel.setFont(QFont("Arial", 14))
        layout.addWidget(viewsLabel, alignment=Qt.AlignCenter)
       

      

        self.setLayout(layout)
class PaymentMethodDialog(QDialog):
    def __init__(self, dbManager, username, parent=None):
        super().__init__(parent)
        self.dbManager = dbManager
        self.username = username
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Aggiungi Metodo di Pagamento")
        layout = QFormLayout()

        self.tipoCombo = QComboBox()
        self.tipoCombo.addItems(["Carta", "Portafoglio"])
        self.tipoCombo.currentTextChanged.connect(self.switchForm)
        layout.addRow("Tipo:", self.tipoCombo)

        self.formStack = QStackedWidget()

        self.cartaWidget = QWidget()
        formCarta = QFormLayout()
        self.nomeCartaEdit = QLineEdit()
        self.numeroCartaEdit = QLineEdit()
        formCarta.addRow("Nome Carta:", self.nomeCartaEdit)
        formCarta.addRow("Numero Carta:", self.numeroCartaEdit)
        self.cartaWidget.setLayout(formCarta)
        self.formStack.addWidget(self.cartaWidget)

        self.portafoglioWidget = QWidget()
        formPortafoglio = QFormLayout()
        self.creditoEdit = QLineEdit()
        self.creditoEdit.setPlaceholderText("Inserisci il credito iniziale")
        formPortafoglio.addRow("Credito Iniziale:", self.creditoEdit)
        self.portafoglioWidget.setLayout(formPortafoglio)
        self.formStack.addWidget(self.portafoglioWidget)

        layout.addRow(self.formStack)

        self.addButton = QPushButton("Aggiungi Metodo")
        self.addButton.clicked.connect(self.addMethod)
        layout.addRow(self.addButton)

        self.setLayout(layout)
        self.switchForm(self.tipoCombo.currentText())

    def switchForm(self, tipo):
        if tipo == "Carta":
            self.formStack.setCurrentIndex(0)
        else:
            self.formStack.setCurrentIndex(1)

    def addMethod(self):
        tipo = self.tipoCombo.currentText()
        if tipo == "Carta":
            nomeCarta = self.nomeCartaEdit.text().strip()
            numeroCarta = self.numeroCartaEdit.text().strip()
            if not nomeCarta or not numeroCarta:
                QMessageBox.warning(self, "Errore", "Compilare tutti i campi per la carta!")
                return
            success, msg = self.dbManager.addPaymentMethod(self.username, tipo, nomeCarta, numeroCarta)
        else:
            credito_text = self.creditoEdit.text().strip()
            try:
                ammontare = float(credito_text)
            except ValueError:
                QMessageBox.warning(self, "Errore", "Il credito deve essere un numero!")
                return
            success, msg = self.dbManager.addPaymentMethod(self.username, tipo, ammontare=ammontare)
        if success:
            QMessageBox.information(self, "Successo", msg)
            self.accept()
        else:
            QMessageBox.critical(self, "Errore", msg)
class ProfiloTab(QWidget):
    def __init__(self, dbManager, loggedUser, onBackToCatalogo=None):
        super().__init__()
        self.dbManager = dbManager
        self.loggedUser = loggedUser
        self.onBackToCatalogo = onBackToCatalogo
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
  
           
        header = QLabel("Profilo Utente")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(header)

        query = "SELECT * FROM Utente WHERE Username = %s;"
        self.dbManager.cursor.execute(query, (self.loggedUser,))
        user = self.dbManager.cursor.fetchone()
        if user:
            info = (f"Username: {user['Username']}\nNome: {user['Nome']}\n"
                    f"Cognome: {user['Cognome']}\nCittà: {user['Citta']}\nIndirizzo: {user['Indirizzo']}")
        else:
            info = "Informazioni utente non trovate."
        self.infoLabel = QLabel(info)
        layout.addWidget(self.infoLabel)

        methodsHeader = QHBoxLayout()
        methodsLabel = QLabel("Metodi di Pagamento:")
        methodsLabel.setFont(QFont("Arial", 14, QFont.Bold))
        methodsHeader.addWidget(methodsLabel)
        methodsHeader.addStretch()
        addMethodButton = QPushButton("Aggiungi Metodo")
        addMethodButton.clicked.connect(self.openAddMethodDialog)
        methodsHeader.addWidget(addMethodButton)
        layout.addLayout(methodsHeader)

        self.methodsText = QTextEdit()
        self.methodsText.setReadOnly(True)
        layout.addWidget(self.methodsText)
        self.loadPaymentMethods()

        self.setLayout(layout)

    def loadPaymentMethods(self):
        methods = self.dbManager.getPaymentMethods(self.loggedUser)
        text = ""
        for m in methods:
            if m["Tipo"] == "Portafoglio":
                text += f"ID:{m['ID']} - {m['Tipo']} (Credito: {m.get('Ammontare',0)})\n"
            else:
                text += f"ID:{m['ID']} - {m['Tipo']}\n"
        self.methodsText.setText(text)

    def openAddMethodDialog(self):
        dialog = PaymentMethodDialog(self.dbManager, self.loggedUser)
        if dialog.exec_():
            self.loadPaymentMethods()
class MainAppPage(QWidget):
    def __init__(self, dbManager, loggedUser, onLogout):
        super().__init__()
        self.dbManager = dbManager
        self.loggedUser = loggedUser
        self.onLogout = onLogout
        self.initUI()

    def initUI(self):
        mainLayout = QVBoxLayout()

        headerLayout = QHBoxLayout()
        catalogoButton = QPushButton("Catalogo")
        catalogoButton.clicked.connect(self.showCatalogo)
        profileButton = QPushButton("Profilo")
        profileButton.clicked.connect(self.showProfilo)
        logoutButton = QPushButton("Logout")
        logoutButton.clicked.connect(self.onLogout)
        headerLayout.addWidget(catalogoButton)
        headerLayout.addWidget(profileButton)
        headerLayout.addStretch()
        headerLayout.addWidget(logoutButton)
        mainLayout.addLayout(headerLayout)

        self.stack = QStackedWidget()
        self.catalogoPage = CatalogoTab(self.dbManager, self.loggedUser)
        self.profiloPage = ProfiloTab(self.dbManager, self.loggedUser, onBackToCatalogo=self.showCatalogo)
        self.stack.addWidget(self.catalogoPage)
        self.stack.addWidget(self.profiloPage)
        mainLayout.addWidget(self.stack)

        self.setLayout(mainLayout)

    def showCatalogo(self):
        self.stack.setCurrentWidget(self.catalogoPage)

    def showProfilo(self):
        self.stack.setCurrentWidget(self.profiloPage)
class AppMainWindow(QMainWindow):
    def __init__(self, dbManager):
        super().__init__()
        self.dbManager = dbManager
        self.setWindowTitle("Piattaforma di Streaming - Demo")
        self.resize(1100, 750)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.initUI()

    def initUI(self):
        self.loginPage = LoginPage(self.dbManager, self.loginSuccess, self.showRegistrationPage)
        self.stack.addWidget(self.loginPage)
        self.stack.setCurrentWidget(self.loginPage)

    def loginSuccess(self, username):
        self.mainAppPage = MainAppPage(self.dbManager, username, self.logout)
        self.stack.addWidget(self.mainAppPage)
        self.stack.setCurrentWidget(self.mainAppPage)

    def showRegistrationPage(self):
        self.registrationPage = RegistrationPage(self.dbManager, self.loginSuccess, self.showLoginPage)
        self.stack.addWidget(self.registrationPage)
        self.stack.setCurrentWidget(self.registrationPage)

    def showLoginPage(self):
        self.stack.setCurrentWidget(self.loginPage)

    def logout(self):
        self.stack.setCurrentWidget(self.loginPage)
def main():
    dbManager = DatabaseManager(host="localhost", user="root", password="yourpassword", database="streaming")
    dbManager.populateMockData()

    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QMainWindow { background-color: #f0f0f0; }
        QWidget { font-family: 'Segoe UI', sans-serif; font-size: 12pt; }
        QLabel { color: #333333; }
        QScrollArea { background-color: transparent; }
        QLineEdit, QComboBox, QDateEdit, QTextEdit { padding: 6px; border: 1px solid #cccccc; border-radius: 4px; }
        QPushButton { background-color: #0078d7; color: #ffffff; padding: 8px 16px; border: none; border-radius: 4px; }
        QPushButton:hover { background-color: #005a9e; }
    """)
    mainWin = AppMainWindow(dbManager)
    mainWin.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
