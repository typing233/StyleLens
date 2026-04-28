import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Switch,
  Button,
  message,
  Space,
  Alert,
  Tag,
  Typography
} from 'antd';
import {
  SettingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  DeleteOutlined,
  CloudServerOutlined
} from '@ant-design/icons';
import { llmConfigApi } from '../services/api';

const { Text } = Typography;

const LLMConfig = ({ onConfigChange }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [currentStatus, setCurrentStatus] = useState(null);
  const [testResult, setTestResult] = useState(null);

  useEffect(() => {
    loadCurrentConfig();
  }, []);

  const loadCurrentConfig = async () => {
    try {
      const status = await llmConfigApi.getStatus();
      setCurrentStatus(status);
      
      if (status.configured) {
        const config = await llmConfigApi.getConfig();
        form.setFieldsValue({
          base_url: config.base_url || '',
          api_key: '',
          model_name: config.model_name || '',
          enabled: config.enabled || false
        });
      }
    } catch (error) {
      console.error('Failed to load LLM config:', error);
    }
  };

  const handleSave = async (values) => {
    setLoading(true);
    try {
      const result = await llmConfigApi.configure(values);
      message.success('LLM configuration saved successfully');
      setCurrentStatus({ configured: values.enabled, message: result.message });
      setTestResult(null);
      
      if (onConfigChange) {
        onConfigChange(values);
      }
    } catch (error) {
      message.error('Failed to save configuration: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async () => {
    try {
      const values = await form.validateFields();
      setTesting(true);
      setTestResult(null);
      
      const result = await llmConfigApi.testConnection(values);
      setTestResult(result);
      
      if (result.success) {
        message.success('Connection test passed!');
      } else {
        message.error('Connection test failed: ' + result.message);
      }
    } catch (error) {
      message.error('Validation failed: ' + (error.errorFields?.[0]?.errors?.[0] || error.message));
    } finally {
      setTesting(false);
    }
  };

  const handleClearConfig = async () => {
    try {
      await llmConfigApi.clearConfig();
      form.resetFields();
      setCurrentStatus({ configured: false, message: 'LLM configuration cleared' });
      setTestResult(null);
      message.success('Configuration cleared');
      
      if (onConfigChange) {
        onConfigChange(null);
      }
    } catch (error) {
      message.error('Failed to clear configuration');
    }
  };

  return (
    <Card
      title={
        <Space>
          <SettingOutlined />
          <span>LLM Configuration (OpenAI Compatible)</span>
          {currentStatus && (
            <Tag icon={currentStatus.configured ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
              color={currentStatus.configured ? 'success' : 'default'}>
              {currentStatus.configured ? 'Configured' : 'Not Configured'}
            </Tag>
          )}
        </Space>
      }
      className="llm-config-card"
    >
      <Alert
        message="About LLM Integration"
        description="Configure your OpenAI-compatible API to enable AI-powered CSS analysis and automatic refactoring suggestions. Supports any provider with OpenAI-compatible API format."
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSave}
        initialValues={{
          base_url: '',
          api_key: '',
          model_name: '',
          enabled: false
        }}
      >
        <Form.Item
          name="enabled"
          label="Enable LLM Integration"
          valuePropName="checked"
        >
          <Switch
            checkedChildren="Enabled"
            unCheckedChildren="Disabled"
          />
        </Form.Item>

        <Form.Item
          name="base_url"
          label={
            <Space>
              <CloudServerOutlined />
              <span>Base URL</span>
            </Space>
          }
          rules={[
            { required: true, message: 'Please enter the API base URL' },
            { type: 'url', message: 'Please enter a valid URL' }
          ]}
          extra="e.g., https://api.openai.com/v1 or your custom endpoint"
        >
          <Input
            placeholder="https://api.openai.com/v1"
            size="large"
          />
        </Form.Item>

        <Form.Item
          name="api_key"
          label="API Key"
          rules={[{ required: true, message: 'Please enter the API key' }]}
          extra="Your API key will be sent securely to the configured endpoint"
        >
          <Input.Password
            placeholder="sk-..."
            size="large"
          />
        </Form.Item>

        <Form.Item
          name="model_name"
          label="Model Name"
          rules={[{ required: true, message: 'Please enter the model name' }]}
          extra="e.g., gpt-3.5-turbo, gpt-4, claude-3-opus, etc."
        >
          <Input
            placeholder="gpt-3.5-turbo"
            size="large"
          />
        </Form.Item>

        {testResult && (
          <Form.Item>
            <Alert
              message={testResult.success ? 'Connection Successful' : 'Connection Failed'}
              description={
                <div>
                  <p><Text strong>Message:</Text> {testResult.message}</p>
                  {testResult.model_info && (
                    <p><Text strong>Model:</Text> {testResult.model_info.model}</p>
                  )}
                </div>
              }
              type={testResult.success ? 'success' : 'error'}
              showIcon
            />
          </Form.Item>
        )}

        <Form.Item>
          <Space>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              size="large"
            >
              Save Configuration
            </Button>
            <Button
              onClick={handleTestConnection}
              loading={testing}
              size="large"
            >
              Test Connection
            </Button>
            <Button
              danger
              icon={<DeleteOutlined />}
              onClick={handleClearConfig}
              size="large"
            >
              Clear Config
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default LLMConfig;
