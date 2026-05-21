(function(global) {
    'use strict';

    function renderWireDomXmlForm(context) {
        if (!context || !context.modalBody) {
            return false;
        }

        var modalBody = context.modalBody;
        var fileType = String(context.fileType || 'WebSeries Wire DOM XML');
        var createTagGroup = context.createTagGroup;
        var openMigrationAddressPopup = context.openMigrationAddressPopup;
        var restoreGenerateFormState = context.restoreGenerateFormState;
        var setGenerateTagValues = context.setGenerateTagValues;
        var setMigrationAddressRows = context.setMigrationAddressRows;
        var hydrateMigrationAddressRowsFromHiddenField = context.hydrateMigrationAddressRowsFromHiddenField;
        var updateGenerateButtonState = context.updateGenerateButtonState;
        var defaultMigrationRows = Array.isArray(context.defaultMigrationRows) ? context.defaultMigrationRows : [];

        var wsLeftColumn = document.createElement('div');
        wsLeftColumn.className = 'formColumn';
        wsLeftColumn.style.borderRight = '1px solid #555';
        wsLeftColumn.style.paddingRight = '15px';

        var wsMiddleColumn = document.createElement('div');
        wsMiddleColumn.className = 'formColumn';
        wsMiddleColumn.style.borderRight = '1px solid #555';
        wsMiddleColumn.style.paddingRight = '15px';

        var wsRightColumn = document.createElement('div');
        wsRightColumn.className = 'formColumn';

        createTagGroup(wsLeftColumn, 'Batches Count', 'wsTransactionsCount', 'Enter number...', false, { singleValueOnly: true, numericOnly: true });

        var companyBankLabel = document.createElement('div');
        companyBankLabel.style.fontSize = '14px';
        companyBankLabel.style.fontWeight = '600';
        companyBankLabel.style.color = '#ffffff';
        companyBankLabel.style.marginTop = '16px';
        companyBankLabel.style.marginBottom = '12px';
        companyBankLabel.textContent = 'Company Bank Info';
        wsLeftColumn.appendChild(companyBankLabel);

        createTagGroup(wsLeftColumn, 'Account Number', 'wsAccountNumber', 'Enter number...', true);
        createTagGroup(wsLeftColumn, 'Increment', 'wsIncrement', 'Enter increment...', true, { singleValueOnly: true, numericOnly: true });
        createTagGroup(wsLeftColumn, 'Account Number End', 'wsAccountNumberEnd', 'Enter end number...', true, { singleValueOnly: true, numericOnly: true });
        createTagGroup(wsLeftColumn, 'Originator Name', 'wsOriginatorName', 'Enter originator name...', true, { singleValueOnly: true });
        createTagGroup(wsLeftColumn, 'Bank Name', 'wsBankNameCompany', 'Enter bank name...', true);
        createTagGroup(wsLeftColumn, 'ABAs', 'wsAbas', 'Enter 9-digit ABA...', true, { numericOnly: true, exactLength: 9 });

        var corrBankLabel = document.createElement('div');
        corrBankLabel.style.fontSize = '14px';
        corrBankLabel.style.fontWeight = '600';
        corrBankLabel.style.color = '#ffffff';
        corrBankLabel.style.marginTop = '16px';
        corrBankLabel.style.marginBottom = '12px';
        corrBankLabel.textContent = 'Corresponding Bank Info';
        wsMiddleColumn.appendChild(corrBankLabel);

        createTagGroup(wsMiddleColumn, 'AddressLine3', 'wsAddressLine3', 'Enter address...', true);
        createTagGroup(wsMiddleColumn, 'State', 'wsState', 'Enter state...', true);
        createTagGroup(wsMiddleColumn, 'BankID', 'wsBankID', 'Enter bank ID...', true);
        createTagGroup(wsMiddleColumn, 'BankRoutingABA', 'wsBankRoutingABA', 'Enter routing ABA...', true);
        createTagGroup(wsMiddleColumn, 'BankName', 'wsBankNameCorr', 'Enter bank name...', true);

        createTagGroup(wsRightColumn, 'Client Company', 'wsClientCompany', 'Enter client company...', false, { singleValueOnly: true });
        createTagGroup(wsRightColumn, 'UserId', 'wsUserId', 'Enter user id...', false, { singleValueOnly: true });

        var migrationGroup = document.createElement('div');
        migrationGroup.className = 'formGroup';

        var migrationLabel = document.createElement('label');
        migrationLabel.className = 'formLabel';
        migrationLabel.textContent = 'Migration Address Fields:';

        var migrationButton = document.createElement('button');
        migrationButton.type = 'button';
        migrationButton.className = 'generateBtn migrationAddressOpenBtn';
        migrationButton.textContent = 'Open';
        migrationButton.style.flex = '0 0 auto';
        migrationButton.addEventListener('click', function() {
            openMigrationAddressPopup(fileType);
        });

        migrationGroup.appendChild(migrationLabel);
        migrationGroup.appendChild(migrationButton);
        wsRightColumn.appendChild(migrationGroup);

        var payeeBankLabel = document.createElement('div');
        payeeBankLabel.style.fontSize = '14px';
        payeeBankLabel.style.fontWeight = '600';
        payeeBankLabel.style.color = '#ffffff';
        payeeBankLabel.style.marginTop = '16px';
        payeeBankLabel.style.marginBottom = '12px';
        payeeBankLabel.textContent = 'Payee Bank Info';
        wsRightColumn.appendChild(payeeBankLabel);

        createTagGroup(wsRightColumn, 'Bank Account Number', 'wsPayeeBankAccountNumber', 'Enter account number...', true);
        createTagGroup(wsRightColumn, 'BankID', 'wsPayeeBankID', 'Enter bank ID...', true);
        createTagGroup(wsRightColumn, 'Bank Name', 'wsPayeeBankName', 'Enter bank name...', true);
        createTagGroup(wsRightColumn, 'BankRoutingABA', 'wsPayeeBankRoutingABA', 'Enter routing ABA...', true);

        var migrationHiddenField = document.createElement('input');
        migrationHiddenField.type = 'hidden';
        migrationHiddenField.name = 'migrationAddressFields';
        wsRightColumn.appendChild(migrationHiddenField);

        modalBody.appendChild(wsLeftColumn);
        modalBody.appendChild(wsMiddleColumn);
        modalBody.appendChild(wsRightColumn);

        var hasRestoredState = restoreGenerateFormState(fileType);
        if (!hasRestoredState) {
            var wsDefaultValues = {
                wsTransactionsCount: [String(defaultMigrationRows.length)],
                wsAccountNumber: ['11223344'],
                wsIncrement: ['0'],
                wsOriginatorName: ['Originator Name'],
                wsBankNameCompany: ['BOA'],
                wsAbas: ['021000018'],
                wsClientCompany: ['RISKUG'],
                wsUserId: ['RISK1'],
                wsPayeeBankAccountNumber: ['1234567890'],
                wsPayeeBankID: ['021000018'],
                wsPayeeBankName: ['WACHOVIA BANK,  NA'],
                wsPayeeBankRoutingABA: ['011101024'],
                wsAddressLine3: ['BOSTON'],
                wsState: ['MA'],
                wsBankID: ['011000015'],
                wsBankNameCorr: ['FEDERAL RESERVE BANK OF BOSTON'],
                wsBankRoutingABA: ['021000018']
            };
            Object.entries(wsDefaultValues).forEach(function(entry) {
                setGenerateTagValues(entry[0], entry[1]);
            });
            setMigrationAddressRows(defaultMigrationRows, fileType);
        }

        hydrateMigrationAddressRowsFromHiddenField(fileType);
        updateGenerateButtonState();
        return true;
    }

    global.WebSeriesWireDomXmlUI = {
        renderWireDomXmlForm: renderWireDomXmlForm
    };
})(window);

