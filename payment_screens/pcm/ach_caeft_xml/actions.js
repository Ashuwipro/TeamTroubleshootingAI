(function(global) {
    'use strict';

    function resolveResponseErrorMessage(response, fallbackMessage) {
        return response.json()
            .then(function(errorData) {
                return errorData && errorData.error ? errorData.error : fallbackMessage;
            })
            .catch(function() {
                return fallbackMessage;
            });
    }

    function extractDownloadFilename(response) {
        var contentDisposition = response.headers.get('Content-Disposition') || '';
        var filenameMatch = contentDisposition.match(/filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i);
        return filenameMatch
            ? decodeURIComponent((filenameMatch[1] || filenameMatch[2] || '').trim())
            : '';
    }

    function buildFallbackFilename(context) {
        var data = context && context.data ? context.data : {};
        var formsPayload = context && Array.isArray(context.formsPayload) ? context.formsPayload : [];
        var firstData = formsPayload[0] || data;
        var clientCompany = firstData.clientCompany || 'ClientCompany';
        var bankName = firstData.bankName || 'BankName';
        var now = new Date();
        var date = now.toISOString().split('T')[0].replace(/-/g, '');
        var time = now.toTimeString().split(' ')[0].replace(/:/g, '');
        return clientCompany + '_' + bankName + '_ACH_CAEFT_' + date + '_' + time + '.xml';
    }

    async function previewAchCaeftXmlFile(context) {
        var data = context && context.data ? context.data : {};
        var fileType = context && context.fileType ? context.fileType : 'ACH CAEFT XML';
        var addMessage = context && context.addMessage ? context.addMessage : function() {};
        var showGeneratePreviewModal = context && context.showGeneratePreviewModal ? context.showGeneratePreviewModal : function() {};
        var getGeneratePreviewTitle = context && context.getGeneratePreviewTitle ? context.getGeneratePreviewTitle : function() { return 'ACH CAEFT XML Preview'; };

        try {
            var response = await fetch('/preview-file', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                addMessage('Error: ' + await resolveResponseErrorMessage(response, 'Unable to preview file'), false);
                return;
            }

            var previewData = await response.json();
            showGeneratePreviewModal(getGeneratePreviewTitle(fileType, data), previewData.content || '');
        } catch (error) {
            addMessage('Error: ' + error.message, false);
        }
    }

    async function generateAchCaeftXmlFile(context) {
        var data = context && context.data ? context.data : {};
        var addMessage = context && context.addMessage ? context.addMessage : function() {};
        var showSuccessPopup = context && context.showSuccessPopup ? context.showSuccessPopup : function() {};

        try {
            var response = await fetch('/generate-xml', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                addMessage('Error: ' + await resolveResponseErrorMessage(response, 'Unable to generate file'), false);
                return;
            }

            var blob = await response.blob();
            var url = window.URL.createObjectURL(blob);
            var filename = extractDownloadFilename(response) || buildFallbackFilename(context);
            showSuccessPopup(filename, url);
        } catch (error) {
            addMessage('Error: ' + error.message, false);
        }
    }

    global.PcmAchCaeftXmlActions = {
        previewAchCaeftXmlFile: previewAchCaeftXmlFile,
        generateAchCaeftXmlFile: generateAchCaeftXmlFile
    };
})(window);

