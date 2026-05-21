(function(global) {
    'use strict';

    function renderWireIntlXmlForm(context) {
        if (!context || !context.modalBody) {
            return false;
        }

        var modalBody = context.modalBody;
        var fileType = String(context.fileType || 'WebSeries Wire INTL XML');
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

        createTagGroup(wsLeftColumn, 'Batches Count', 'wsIntlTransactionsCount', 'Enter number...', false, { singleValueOnly: true, numericOnly: true });

        var companyBankLabel = document.createElement('div');
        companyBankLabel.style.fontSize = '14px';
        companyBankLabel.style.fontWeight = '600';
        companyBankLabel.style.color = '#ffffff';
        companyBankLabel.style.marginTop = '16px';
        companyBankLabel.style.marginBottom = '12px';
        companyBankLabel.textContent = 'Company Bank Info';
        wsLeftColumn.appendChild(companyBankLabel);

        createTagGroup(wsLeftColumn, 'Account Number', 'wsIntlAccountNumber', 'Enter number...', true);
        createTagGroup(wsLeftColumn, 'Increment', 'wsIntlIncrement', 'Enter increment...', true, { singleValueOnly: true, numericOnly: true });
        createTagGroup(wsLeftColumn, 'Account Number End', 'wsIntlAccountNumberEnd', 'Enter end number...', true, { singleValueOnly: true, numericOnly: true });
        createTagGroup(wsLeftColumn, 'Originator Name', 'wsIntlOriginatorName', 'Enter originator name...', true, { singleValueOnly: true });
        createTagGroup(wsLeftColumn, 'Bank Name', 'wsIntlBankNameCompany', 'Enter bank name...', true);
        createTagGroup(wsLeftColumn, 'ABAs', 'wsIntlAbas', 'Enter 9-digit ABA...', true, { numericOnly: true, exactLength: 9 });

        var corrBankLabel = document.createElement('div');
        corrBankLabel.style.fontSize = '14px';
        corrBankLabel.style.fontWeight = '600';
        corrBankLabel.style.color = '#ffffff';
        corrBankLabel.style.marginTop = '16px';
        corrBankLabel.style.marginBottom = '12px';
        corrBankLabel.textContent = 'Corresponding Bank Info';
        wsMiddleColumn.appendChild(corrBankLabel);

        createTagGroup(wsMiddleColumn, 'AddressLine3', 'wsIntlAddressLine3', 'Enter address...', true);
        createTagGroup(wsMiddleColumn, 'State', 'wsIntlState', 'Enter state...', true);
        createTagGroup(wsMiddleColumn, 'BankID', 'wsIntlBankID', 'Enter bank ID...', true);
        createTagGroup(wsMiddleColumn, 'BankRoutingABA', 'wsIntlBankRoutingABA', 'Enter routing ABA...', true);
        createTagGroup(wsMiddleColumn, 'BankName', 'wsIntlBankNameCorr', 'Enter bank name...', true);

        createTagGroup(wsRightColumn, 'Client Company', 'wsIntlClientCompany', 'Enter client company...', false, { singleValueOnly: true });
        createTagGroup(wsRightColumn, 'UserId', 'wsIntlUserId', 'Enter user id...', false, { singleValueOnly: true });

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

        createTagGroup(wsRightColumn, 'Bank Account Number', 'wsIntlPayeeBankAccountNumber', 'Enter account number...', true);
        createTagGroup(wsRightColumn, 'BankID', 'wsIntlPayeeBankID', 'Enter bank ID...', true);
        createTagGroup(wsRightColumn, 'Bank Name', 'wsIntlPayeeBankName', 'Enter bank name...', true);
        createTagGroup(wsRightColumn, 'BankRoutingABA', 'wsIntlPayeeBankRoutingABA', 'Enter routing ABA...', true);

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
                wsIntlTransactionsCount: [String(defaultMigrationRows.length)],
                wsIntlAccountNumber: ['11223344'],
                wsIntlIncrement: ['0'],
                wsIntlOriginatorName: ['Originator Name'],
                wsIntlBankNameCompany: ['BOA'],
                wsIntlAbas: ['021000018'],
                wsIntlClientCompany: ['RISKUG'],
                wsIntlUserId: ['RISK1'],
                wsIntlPayeeBankAccountNumber: ['1234567890'],
                wsIntlPayeeBankID: ['021000018'],
                wsIntlPayeeBankName: ['WACHOVIA BANK,  NA'],
                wsIntlPayeeBankRoutingABA: ['011101024'],
                wsIntlAddressLine3: ['BOSTON'],
                wsIntlState: ['MA'],
                wsIntlBankID: ['011000015'],
                wsIntlBankNameCorr: ['FEDERAL RESERVE BANK OF BOSTON'],
                wsIntlBankRoutingABA: ['021000018']
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

    global.WebSeriesWireIntlXmlUI = {
        renderWireIntlXmlForm: renderWireIntlXmlForm
    };
})(window);


