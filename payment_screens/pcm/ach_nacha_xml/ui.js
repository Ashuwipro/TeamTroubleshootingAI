(function(global) {
    'use strict';

    function renderAchNachaXmlForm(context) {
        if (!context || !context.modalBody || typeof context.createTagGroup !== 'function') {
            return false;
        }

        var modalBody = context.modalBody;
        var createTagGroup = context.createTagGroup;
        var setGenerateTagValues = context.setGenerateTagValues || function() {};
        var updateGenerateButtonState = context.updateGenerateButtonState || function() {};
        var requiredAsteriskMarkup = context.requiredAsteriskMarkup || '<span style="color: #ff5555; margin-left: 2px; display: inline-block;">*</span>';

        var leftColumn = document.createElement('div');
        leftColumn.className = 'formColumn';
        leftColumn.style.borderRight = '1px solid #555';
        leftColumn.style.paddingRight = '15px';
        leftColumn.style.display = 'flex';
        leftColumn.style.flexDirection = 'column';

        var middleColumn = document.createElement('div');
        middleColumn.className = 'formColumn';
        middleColumn.style.borderRight = '1px solid #555';
        middleColumn.style.paddingRight = '15px';
        middleColumn.style.display = 'flex';
        middleColumn.style.flexDirection = 'column';

        var rightColumn = document.createElement('div');
        rightColumn.className = 'formColumn';
        rightColumn.style.display = 'flex';
        rightColumn.style.flexDirection = 'column';
        rightColumn.style.justifyContent = 'flex-start';

        // Left Column: Basic Information and Batch/Transaction Config
        var leftHeader = document.createElement('div');
        leftHeader.className = 'formLabel achSectionLabel';
        leftHeader.textContent = 'Batch & Transaction Configuration';
        leftColumn.appendChild(leftHeader);

        createTagGroup(leftColumn, 'Batches Quantity', 'batchesQuantity', 'Enter number of batches...', false, { singleValueOnly: true, numericPositiveOnly: true }, true);
        createTagGroup(leftColumn, 'Transactions Count', 'transactionsCount', 'Enter count(s)...', false, { singleValueOnly: false }, true);

        var paymentTypeHeader = document.createElement('div');
        paymentTypeHeader.className = 'formLabel achSectionLabel';
        paymentTypeHeader.style.marginTop = '20px';
        paymentTypeHeader.textContent = 'Payment Type Information';
        leftColumn.appendChild(paymentTypeHeader);

        var typeSelect = document.createElement('select');
        typeSelect.name = 'type';
        typeSelect.className = 'formSelect';
        typeSelect.style.marginTop = '8px';
        var typeOptions = ['CCD', 'CTX', 'PPD', 'IAT'];
        typeOptions.forEach(function(option) {
            var optionElement = document.createElement('option');
            optionElement.value = option;
            optionElement.textContent = option;
            typeSelect.appendChild(optionElement);
        });
        leftColumn.appendChild(typeSelect);

        var optionsHeader = document.createElement('div');
        optionsHeader.className = 'formLabel';
        optionsHeader.style.marginTop = '12px';
        optionsHeader.textContent = 'Options:';
        leftColumn.appendChild(optionsHeader);

        var optionsSelect = document.createElement('select');
        optionsSelect.name = 'options';
        optionsSelect.className = 'formSelect';
        optionsSelect.style.marginTop = '8px';
        var optionsValues = ['ACH', 'ACH & ESend', 'ESend_Only'];
        optionsValues.forEach(function(option) {
            var optionElement = document.createElement('option');
            optionElement.value = option;
            optionElement.textContent = option;
            optionsSelect.appendChild(optionElement);
        });
        leftColumn.appendChild(optionsSelect);

        // Middle Column: ACH Company Information
        var midHeader = document.createElement('div');
        midHeader.className = 'formLabel achSectionLabel';
        midHeader.textContent = 'ACH Company Information';
        middleColumn.appendChild(midHeader);

        createTagGroup(middleColumn, 'ACH Comp IDs', 'achCompIds', 'Enter company IDs...', false, {}, true);
        createTagGroup(middleColumn, 'ACH Comp Names', 'achCompNames', 'Enter company names...', false, {}, true);
        createTagGroup(middleColumn, 'Client Company', 'clientCompany', 'Enter client company...', false, { singleValueOnly: true }, true);

        var bankHeader = document.createElement('div');
        bankHeader.className = 'formLabel achSectionLabel';
        bankHeader.style.marginTop = '20px';
        bankHeader.textContent = 'Bank Information';
        middleColumn.appendChild(bankHeader);

        createTagGroup(middleColumn, 'ABAs', 'abas', 'Enter ABA numbers...', false, { numericOnly: true, exactLength: 9 }, true);
        createTagGroup(middleColumn, 'Bank Name', 'bankName', 'Enter bank name...', false, { singleValueOnly: true }, true);

        // Right Column: Payee and ESend Information
        var rightHeader = document.createElement('div');
        rightHeader.className = 'formLabel achSectionLabel';
        rightHeader.textContent = 'Payee & ESend Information';
        rightColumn.appendChild(rightHeader);

        createTagGroup(rightColumn, 'Payee IDs', 'payeeIds', 'Enter payee IDs...', false, {}, true);

        var payeeLookupHeader = document.createElement('div');
        payeeLookupHeader.className = 'formLabel';
        payeeLookupHeader.style.marginTop = '12px';
        payeeLookupHeader.textContent = 'Payee Lookup Type:';
        rightColumn.appendChild(payeeLookupHeader);

        var payeeLookupSelect = document.createElement('select');
        payeeLookupSelect.name = 'payeeLookupType';
        payeeLookupSelect.className = 'formSelect';
        payeeLookupSelect.style.marginTop = '8px';
        var lookupTypes = ['No Flag', 'DB', 'FILE', 'NONE'];
        lookupTypes.forEach(function(option) {
            var optionElement = document.createElement('option');
            optionElement.value = option;
            optionElement.textContent = option;
            payeeLookupSelect.appendChild(optionElement);
        });
        rightColumn.appendChild(payeeLookupSelect);

        createTagGroup(rightColumn, 'Payee Lookup Elements', 'payeeLookupElements', 'Enter elements...', false, {}, true);
        createTagGroup(rightColumn, 'Payee Emails', 'payeeEmails', 'Enter email addresses...', false, {}, true);

        var esendHeader = document.createElement('div');
        esendHeader.className = 'formLabel achSectionLabel';
        esendHeader.style.marginTop = '20px';
        esendHeader.textContent = 'ESend Configuration';
        rightColumn.appendChild(esendHeader);

        var esendAppTypeHeader = document.createElement('div');
        esendAppTypeHeader.className = 'formLabel';
        esendAppTypeHeader.style.marginTop = '12px';
        esendAppTypeHeader.textContent = 'ESend App Type:';
        rightColumn.appendChild(esendAppTypeHeader);

        var esendAppTypeSelect = document.createElement('select');
        esendAppTypeSelect.name = 'esendAppType';
        esendAppTypeSelect.className = 'formSelect';
        esendAppTypeSelect.style.marginTop = '8px';
        var appTypes = ['Name', 'ID'];
        appTypes.forEach(function(option) {
            var optionElement = document.createElement('option');
            optionElement.value = option;
            optionElement.textContent = option;
            esendAppTypeSelect.appendChild(optionElement);
        });
        rightColumn.appendChild(esendAppTypeSelect);

        createTagGroup(rightColumn, 'ESend App Value', 'esendAppValue', 'Enter app value...', false, {}, true);
        createTagGroup(rightColumn, 'ESend Profile Keys', 'esendProfileKeys', 'Enter profile keys...', false, {}, true);

        var caeftHeader = document.createElement('div');
        caeftHeader.className = 'formLabel achSectionLabel';
        caeftHeader.style.marginTop = '20px';
        caeftHeader.textContent = 'CAEFT Information (Optional)';
        rightColumn.appendChild(caeftHeader);

        createTagGroup(rightColumn, 'Funding Account Number', 'fundingAccountNumber', 'Enter funding account...', false, { singleValueOnly: true }, true);
        createTagGroup(rightColumn, 'Return Account Number', 'returnAccountNumber', 'Enter return account...', false, { singleValueOnly: true }, true);
        createTagGroup(rightColumn, 'Account Number', 'accountNumber', 'Enter account number...', false, { singleValueOnly: true }, true);

        var creditDebitHeader = document.createElement('div');
        creditDebitHeader.className = 'formLabel';
        creditDebitHeader.style.marginTop = '12px';
        creditDebitHeader.textContent = 'Batch Credit/Debit:';
        rightColumn.appendChild(creditDebitHeader);

        var batchCreditDebitSelect = document.createElement('select');
        batchCreditDebitSelect.name = 'batchCreditDebit';
        batchCreditDebitSelect.className = 'formSelect';
        batchCreditDebitSelect.style.marginTop = '8px';
        var creditDebitOptions = ['Credit', 'Debit'];
        creditDebitOptions.forEach(function(option) {
            var optionElement = document.createElement('option');
            optionElement.value = option;
            optionElement.textContent = option;
            batchCreditDebitSelect.appendChild(optionElement);
        });
        rightColumn.appendChild(batchCreditDebitSelect);

        var tranCreditDebitHeader = document.createElement('div');
        tranCreditDebitHeader.className = 'formLabel';
        tranCreditDebitHeader.style.marginTop = '12px';
        tranCreditDebitHeader.textContent = 'Transaction Credit/Debit:';
        rightColumn.appendChild(tranCreditDebitHeader);

        var tranCreditDebitSelect = document.createElement('select');
        tranCreditDebitSelect.name = 'transactionCreditDebit';
        tranCreditDebitSelect.className = 'formSelect';
        tranCreditDebitSelect.style.marginTop = '8px';
        creditDebitOptions.forEach(function(option) {
            var optionElement = document.createElement('option');
            optionElement.value = option;
            optionElement.textContent = option;
            tranCreditDebitSelect.appendChild(optionElement);
        });
        rightColumn.appendChild(tranCreditDebitSelect);

        modalBody.appendChild(leftColumn);
        modalBody.appendChild(middleColumn);
        modalBody.appendChild(rightColumn);

        updateGenerateButtonState();
        return true;
    }

    global.PcmAchNachaXmlUI = {
        renderAchNachaXmlForm: renderAchNachaXmlForm
    };
})(window);


