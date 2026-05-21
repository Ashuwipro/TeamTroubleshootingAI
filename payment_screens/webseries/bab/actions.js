(function(global) {
    'use strict';

    async function previewBab(context) {
        var data = context && context.data ? context.data : {};
        var addMessage = context && context.addMessage ? context.addMessage : function() {};
        var showGeneratePreviewModal = context && context.showGeneratePreviewModal ? context.showGeneratePreviewModal : function() {};
        var getGeneratePreviewTitle = context && context.getGeneratePreviewTitle ? context.getGeneratePreviewTitle : function() { return 'BAB Preview'; };
        var fileType = context && context.fileType ? context.fileType : 'WebSeries BAB';

        try {
            var response = await fetch('/preview-file', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                var errorData = await response.json();
                addMessage('Error: ' + (errorData.error || 'Unable to preview file'), false);
                return;
            }

            var previewData = await response.json();
            showGeneratePreviewModal(getGeneratePreviewTitle(fileType, data), previewData.content || '');
        } catch (error) {
            addMessage('Error: ' + error.message, false);
        }
    }

    async function generateBab(context) {
        var data = context && context.data ? context.data : {};
        var formsPayload = context && Array.isArray(context.formsPayload) ? context.formsPayload : [];
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
                var errorData = await response.json();
                addMessage('Error: ' + (errorData.error || 'Unable to generate file'), false);
                return;
            }

            var blob = await response.blob();
            var url = window.URL.createObjectURL(blob);

            var contentDisposition = response.headers.get('Content-Disposition') || '';
            var filenameMatch = contentDisposition.match(/filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i);
            var backendFilename = filenameMatch
                ? decodeURIComponent((filenameMatch[1] || filenameMatch[2] || '').trim())
                : '';

            var firstData = formsPayload[0] || data;
            var userGroup = firstData.clientCompany || 'UNKNOWN';
            var bankName = firstData.bankName || 'UNKNOWN';
            var now = new Date();
            var date = now.toISOString().split('T')[0].replace(/-/g, '');
            var time = now.toTimeString().split(' ')[0].replace(/:/g, '');
            var fallbackExtension = (firstData.fileType === 'ACH FILE') ? '.ACH' : '.xml';
            var fallbackFilename = userGroup + '_' + bankName + '_ACHXML_' + date + '_' + time + fallbackExtension;
            var filename = backendFilename || fallbackFilename;

            showSuccessPopup(filename, url);
        } catch (error) {
            addMessage('Error: ' + error.message, false);
        }
    }

    global.WebSeriesBabActions = {
        previewBab: previewBab,
        generateBab: generateBab
    };
})(window);



