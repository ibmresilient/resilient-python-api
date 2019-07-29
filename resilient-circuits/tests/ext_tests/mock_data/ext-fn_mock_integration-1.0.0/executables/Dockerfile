FROM resilient:v33

ENV FN_MOCK_INTEGRATION_MOCK_CONFIG_URL=''
ENV FN_MOCK_INTEGRATION_MOCK_CONFIG_USERNAME=''
ENV FN_MOCK_INTEGRATION_MOCK_CONFIG_PASSWORD=''

COPY *.tar.gz /app/data

RUN pip install -U fn_mock_integration-1.0.0.tar.gz 
 && resilient-circuits config -u -l fn-mock-integration
 && sed -i "s/mock_config_url=https://api.example.com/mock_config_url=\$FN_MOCK_INTEGRATION_MOCK_CONFIG_URL/g" ~/.resilient/app.config \ 
 && sed -i "s/mock_config_username=aryastark@example.com/mock_config_username=\$FN_MOCK_INTEGRATION_MOCK_CONFIG_USERNAME/g" ~/.resilient/app.config \ 
 && sed -i "s/mock_config_password=TheK!ghtKing/mock_config_password=\$FN_MOCK_INTEGRATION_MOCK_CONFIG_PASSWORD/g" ~/.resilient/app.config  

ENTRYPOINT /app/bin/res_start.exp