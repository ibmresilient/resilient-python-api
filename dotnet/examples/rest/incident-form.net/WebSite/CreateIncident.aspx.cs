/*
 * Resilient Systems, Inc. ("Resilient") is willing to license software
 * or access to software to the company or entity that will be using or
 * accessing the software and documentation and that you represent as
 * an employee or authorized agent ("you" or "your") only on the condition
 * that you accept all of the terms of this license agreement.
 *
 * The software and documentation within Resilient's Development Kit are
 * copyrighted by and contain confidential information of Resilient. By
 * accessing and/or using this software and documentation, you agree that
 * while you may make derivative works of them, you:
 *
 * 1)  will not use the software and documentation or any derivative
 *     works for anything but your internal business purposes in
 *     conjunction your licensed used of Resilient's software, nor
 * 2)  provide or disclose the software and documentation or any
 *     derivative works to any third party.
 *
 * THIS SOFTWARE AND DOCUMENTATION IS PROVIDED "AS IS" AND ANY EXPRESS
 * OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL RESILIENT BE LIABLE FOR ANY DIRECT,
 * INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 */


using System.Globalization;
using System.Linq;
using System.Net;
using Co3.Rest;
using Co3.Rest.Dto;
using Newtonsoft.Json;
using Resources;
using System;
using System.Collections.Generic;
using System.Configuration;
using System.IO;
using System.Reflection;
using System.Web.UI;
using System.Web.UI.WebControls;

public partial class CreateIncident : System.Web.UI.Page
{
    const string FieldPrefix = "co3_";

    // List of <ContentPlaceHolder> tags in the master files.  If master files
    // are being used, we would need to iterate through the content place
    // holders to find the Co3 controls.
    List<ContentPlaceHolder> m_contentPlaceHolders;

    // hidden field used to get the UTC offset from the browser so that we can
    // properly calculate the datetime relative to the user.
    HiddenField m_utcOffsetField;

    // a map of field IDs to the corresponding controls on the page
    Dictionary<string, WebControl> m_instantiatedFields;

    // list of field IDs to all available fields received from the server
    Dictionary<string, FieldDefDto> m_fields;

    // REST API session object
    SessionRest m_sessionRest;

    // session info
    UserSessionDto m_sessionInfo;

    float m_utcOffset;

    public CreateIncident()
    {
        m_utcOffset = 0;
    }

    protected override void OnInit(EventArgs e)
    {
        base.OnInit(e);

        // Determine if a master file is being used.  If it is, find all the 
        // ContentPlaceHolders in the master file so that we can look for
        // the controls in the ContentPlaceHolders later.
        if (Master != null)
        {
            m_contentPlaceHolders = new List<ContentPlaceHolder>();
            FindContentPlaceHolders(Master.Controls, m_contentPlaceHolders);
        }
    }

    /// <summary>
    /// Recursive method to find ContentPlaceHolders
    /// </summary>
    /// <param name="controls"></param>
    /// <param name="cph"></param>
    private void FindContentPlaceHolders(ControlCollection controls, List<ContentPlaceHolder> cph)
    {
        foreach (Control control in controls)
        {
            if (control is ContentPlaceHolder)
                cph.Add((ContentPlaceHolder)control);

            if (control.Controls.Count > 0)
                FindContentPlaceHolders(control.Controls, cph);
        }
    }

    protected override void OnLoad(EventArgs e)
    {
        base.OnLoad(e);

        // create a hidden field to store the timezone offset needed to determine
        // the proper local date and time.
        m_utcOffsetField = new HiddenField
        {
            ID = string.Format("{0}{1}time_offset", '_', FieldPrefix)
        };
        Form.Controls.Add(m_utcOffsetField);

        // create JavaScript to capture the timezone offset
        ClientScript.RegisterStartupScript(m_utcOffsetField.GetType(), m_utcOffsetField.ID,
            string.Format("document.getElementById(\"{0}\").value=(new Date()).getTimezoneOffset();", m_utcOffsetField.ClientID), true);

        // create credentials to connect to the REST API
        AuthenticationDto credentials = new AuthenticationDto
        {
            Email = ConfigurationManager.AppSettings["Co3UserAccount"],
            Password = ConfigurationManager.AppSettings["Co3UserPassword"]
        };

        try
        {
            if (string.IsNullOrEmpty(RestEndpoint.Co3ApiUrl))
                throw new ArgumentNullException("Co3ApiUrl", "Please set Co3ApiUrl in AppSettings");

            // connect to the REST API
            m_sessionRest = new SessionRest();
            m_sessionInfo = m_sessionRest.Authenticate(credentials);

            // load the org data
            OrgRest orgRest = m_sessionRest.GetOrgRest();
            FullOrgDto org = orgRest.GetOrg();

            // load field data
            m_fields = new Dictionary<string, FieldDefDto>();
            FieldDefDto[] fieldTypes = m_sessionRest.GetFieldRest().GetFieldTypes(org.Id);

            // create a map of field names to fields for lookups later
            foreach (FieldDefDto fieldDef in fieldTypes)
                m_fields.Add(fieldDef.Name, fieldDef);

            // verify that the control on the page are of the expected
            // data type
            m_instantiatedFields = new Dictionary<string, WebControl>();
            foreach (KeyValuePair<string, FieldDefDto> field in m_fields)
            {
                WebControl ctrl = (WebControl)FindControl(FieldPrefix + field.Key);
                if (ctrl == null)
                    continue;

                switch (field.Value.InputType)
                {
                    case InputType.DatePicker:
                    case InputType.DateTimePicker:
                    case InputType.Number:
                    case InputType.Text:
                    case InputType.TextArea:
                        // these fields must be text boxes
                        if (!(ctrl is TextBox))
                            throw new ArgumentException(string.Format(Strings.InputTypeMismatch,
                                FieldPrefix + field.Key, ctrl.GetType().Name, "TextBox"));
                        break;
                    case InputType.Boolean:
                    case InputType.Select:
                    case InputType.SelectOwner:
                        // these fields must support multiple choices single answer
                        if (!(ctrl is DropDownList) && !(ctrl is RadioButtonList))
                            throw new ArgumentException(string.Format(Strings.InputTypeMismatch,
                                FieldPrefix + field.Key, ctrl.GetType().Name, "DropDownList or RadioButtonList"));
                        break;
                    case InputType.MultiSelect:
                        // these fields must support multiple choices multiple answers
                        if (!(ctrl is CheckBoxList))
                            throw new ArgumentException(string.Format(Strings.InputTypeMismatch,
                                FieldPrefix + field.Key, ctrl.GetType().Name, "CheckBoxList"));
                        break;
                    case InputType.MultiSelectIncident:
                    case InputType.MultiSelectMembers:
                    case InputType.MultiSelectTask:
                    default:
                        throw new NotImplementedException(field.Key + " is not supported");
                }

                m_instantiatedFields.Add(field.Key, ctrl);
            }

            if (!IsPostBack)
                InitializeControls();
        }
        catch (Exception ex)
        {
            HandleException(ex);
        }
    }

    // Implement our own FindControl() so that we can either look on the page
    // of in the content place holders if the page uses master page.
    public override Control FindControl(string id)
    {
        // just a plain page
        if (m_contentPlaceHolders == null)
            return base.FindControl(id);

        // master page is in use, look in content place holders
        Control ctrl = null;
        for (int i = 0; i < m_contentPlaceHolders.Count && ctrl == null; ++i)
            ctrl = m_contentPlaceHolders[i].FindControl(id);

        return ctrl;
    }

    private void HandleException(Exception ex)
    {
        string strMessage = null;
        if (ex is WebException && ((WebException)ex).Response != null)
        {
            using (Stream stream = ((WebException)ex).Response.GetResponseStream())
                if (stream != null)
                    using (StreamReader reader = new StreamReader(stream))
                    {
                        strMessage = reader.ReadToEnd();
                    }
        }

        OnHandleException(ex, strMessage);
    }

    protected virtual void OnHandleException(Exception ex, string message)
    {
        // noop
    }

    // populate controls with data and specify whether they're required
    private void InitializeControls()
    {
        // CSS class added to required fields
        string cssRequired = ConfigurationManager.AppSettings["Co3CssRequired"];

        foreach (KeyValuePair<string, FieldDefDto> field in m_fields)
        {
            WebControl ctrl = (WebControl)FindControl(FieldPrefix + field.Key);

            // this field doesn't have a matching control on the page
            if (ctrl == null)
            {
                // if the field is required, we can't continue.
                if (field.Value.Required == FieldRequired.Always)
                    throw new MissingFieldException(string.Format("{0}{1} is required", FieldPrefix, field.Key));

                continue;
            }

            // add the tool tip
            ctrl.ToolTip = field.Value.Tooltip;

            // add the required CSS class
            if (field.Value.Required == FieldRequired.Always && !string.IsNullOrEmpty(cssRequired))
                ctrl.CssClass += string.Format(" {0}", cssRequired);

            // populate according to the field type
            switch (field.Value.InputType)
            {
                case InputType.Boolean:
                    PopulateBoolean((ListControl)ctrl, field.Value);
                    break;
                case InputType.Text:
                case InputType.TextArea:
                    ctrl.Attributes["placeholder"] = field.Value.Text;
                    break;
                case InputType.MultiSelect:
                case InputType.MultiSelectIncident:
                case InputType.MultiSelectMembers:
                case InputType.MultiSelectTask:
                case InputType.Select:
                case InputType.SelectOwner:
                    PopulateSelect((ListControl)ctrl, field.Value);
                    break;
            }
        }
    }

    private void PopulateBoolean(ListControl list, FieldDefDto field)
    {
        list.Items.Add(new ListItem(string.IsNullOrEmpty(field.LabelTrue) ? Strings.Yes : field.LabelTrue, "1"));
        list.Items.Add(new ListItem(string.IsNullOrEmpty(field.LabelFalse) ? Strings.No : field.LabelFalse, "0"));

        if (field.Required != FieldRequired.Always)
            list.Items.Add(new ListItem(Strings.Unknown, ""));
    }

    private void PopulateSelect(ListControl list, FieldDefDto field)
    {
        foreach (FieldDefValueDto fieldDefValue in field.Values)
        {
            ListItem item = new ListItem(fieldDefValue.Label, fieldDefValue.Value.ToString(), fieldDefValue.Enabled)
            {
                Selected = fieldDefValue.Default
            };
            list.Items.Add(item);
        }
    }

    /// <summary>
    /// Create an incident based on the fields on the page.
    /// </summary>
    /// <param name="incident">An optional incident with pre-populated properties.
    /// The pre-populated properties will override the corresponding fields on the page.</param>
    /// <returns>True if the incident has been created.</returns>
    public bool Co3CreateIncident(FullIncidentDataDto incident)
    {
        float.TryParse(m_utcOffsetField.Value, out m_utcOffset);

        if (incident == null)
            incident = new FullIncidentDataDto();

        if (CollectData(incident) && m_sessionRest != null)
        {
            try
            {
                OrgRest orgRest = m_sessionRest.GetOrgRest();
                FullOrgDto org = orgRest.GetOrg();
                incident.OrgId = org.Id;
                incident.CreateDate = DateTime.UtcNow;
                incident.OwnerId = m_sessionInfo.UserId;
                incident.CreatorId = m_sessionInfo.UserId;
                incident.Regulators = new RegulatorsDto
                {
                    Ids = new List<int>
                    {
                        // 149: Securities incident best practices regulator
                        // This value must be hard coded in order to generate tasks
                        149
                    }
                };

                IncidentDto incidentResult = m_sessionRest.GetIncidentRest().CreateIncident(org.Id, incident, true, false);

                m_sessionRest.LogOut();
                return true;
            }
            catch (Exception ex)
            {
                HandleException(ex);
            }
        }

        return false;
    }

    // collect data from the form
    private bool CollectData(IncidentDto incident)
    {
        bool bValidated = true;
        object value;

        // match the incident object's properties against the fields/controls
        // on the page using reflection
        foreach (PropertyInfo property in incident.GetType().GetProperties(BindingFlags.Instance | BindingFlags.Public))
        {
            JsonPropertyAttribute jsonProperty = property.GetCustomAttribute<JsonPropertyAttribute>();
            if (jsonProperty == null)
                continue;

            // this field is not on the page
            if (!m_instantiatedFields.ContainsKey(jsonProperty.PropertyName))
                continue;

            // this is not an internal or custom field
            if (!m_fields.ContainsKey(jsonProperty.PropertyName))
                continue;

            // get the value from the control
            bValidated &= GetControlValue(
                m_instantiatedFields[jsonProperty.PropertyName],
                m_fields[jsonProperty.PropertyName],
                out value);

            // the value is not in the expected format
            if (!bValidated)
                return false;

            if (value != null)
            {
                // the property has a value, check if it's the default value
                // or one specified by the caller of Co3CreateIncident()
                if (property.PropertyType.IsValueType)
                {
                    // if the property has the default value, then we'll apply
                    // the value we got from the web control.
                    if (Activator.CreateInstance(property.PropertyType)
                        .Equals(property.GetValue(incident)))
                    {
                        property.SetValue(incident, value);
                    }
                }
                else if (property.GetValue(incident) == null)
                    property.SetValue(incident, value);
            }
        }

        // process custom properties
        if (incident.Properties == null)
            incident.Properties = new SortedList<string, object>();

        foreach (KeyValuePair<string, FieldDefDto> field in m_fields)
        {
            if (field.Value.Internal)
                continue;

            if (!m_instantiatedFields.ContainsKey(field.Value.Name))
                continue;

            // we do not overwrite existing data
            if (incident.Properties.ContainsKey(field.Key))
                continue;

            bValidated &= GetControlValue(
                m_instantiatedFields[field.Value.Name], field.Value, out value);
            if (!bValidated)
                return false;

            if (value != null)
                incident.Properties.Add(field.Key, value);
        }

        return bValidated;
    }

    // get the control's value
    private bool GetControlValue(WebControl ctrl, FieldDefDto field, out object value)
    {
        bool bParsed = true;
        value = null;

        switch (field.InputType)
        {
            case InputType.Boolean:
                if (string.IsNullOrEmpty(((ListControl)ctrl).SelectedValue))
                    bParsed = field.Required != FieldRequired.Always;
                else
                    value = ((ListControl)ctrl).SelectedValue == "1";
                break;
            case InputType.DatePicker:
            case InputType.DateTimePicker:
                {
                    if (!string.IsNullOrEmpty(((TextBox)ctrl).Text))
                    {
                        DateTime dt;
                        bParsed = DateTime.TryParseExact(((TextBox)ctrl).Text,
                            "MM/dd/yyyy HH:mm",
                            CultureInfo.CurrentCulture,
                            DateTimeStyles.None,
                            out dt);

                        if (bParsed)
                        {
                            // convert time to UTC because that's what the server expects
                            dt = DateTime.SpecifyKind(dt.AddMinutes(m_utcOffset), DateTimeKind.Utc);

                            if (field.Internal)
                            {
                                // occurred and discovered date cannot be in the future
                                if (new[] { "start_date", "discovered_date" }.Contains(field.Name) && DateTime.UtcNow < dt)
                                    bParsed = false;
                                else
                                    value = dt;
                            }
                            else
                                value = Co3.Rest.JsonConverters.UnixTimeConverter.ToEpochTimeMsec(dt);
                        }
                    }
                    else
                        bParsed = field.Required != FieldRequired.Always;

                    break;
                }
            case InputType.MultiSelect:
                {
                    ListControl list = (ListControl)ctrl;
                    List<string> vecStrValues = new List<string>();

                    for (int j = 0; j < list.Items.Count; ++j)
                    {
                        if (list.Items[j].Selected)
                            vecStrValues.Add(list.Items[j].Value);
                    }

                    if (vecStrValues.Count == 0)
                    {
                        // no selected values, determine if it's required
                        bParsed = field.Required != FieldRequired.Always;
                        break;
                    }

                    // if the field should be a number, convert it to a number
                    if (field.Values[0].Value is long
                        || field.Values[0].Value is int)
                    {
                        value = vecStrValues.Select(int.Parse).ToList();
                    }
                    else
                        value = vecStrValues;
                    break;
                }
            case InputType.MultiSelectIncident:
                break;
            case InputType.MultiSelectMembers:
                break;
            case InputType.MultiSelectTask:
                break;
            case InputType.Number:
                if (!string.IsNullOrEmpty(((TextBox)ctrl).Text))
                {
                    int intValue;
                    bParsed = int.TryParse(((TextBox)ctrl).Text, out intValue);
                    if (bParsed)
                        value = intValue;
                }
                else
                    bParsed = field.Required != FieldRequired.Always;
                break;
            case InputType.Select:
                if (string.IsNullOrEmpty(((ListControl)ctrl).SelectedValue))
                    bParsed = field.Required != FieldRequired.Always;
                else
                {
                    // convert to a number if the field is a number
                    if (field.Values[0].Value is long
                        || field.Values[0].Value is int)
                    {
                        value = int.Parse(((ListControl)ctrl).SelectedValue);
                    }
                    else
                        value = ((ListControl)ctrl).SelectedValue;
                }
                break;
            case InputType.SelectOwner:
                break;
            case InputType.Text:
            case InputType.TextArea:
                if (string.IsNullOrEmpty(((TextBox)ctrl).Text))
                    bParsed = field.Required != FieldRequired.Always;
                else
                    value = ((TextBox)ctrl).Text;
                break;
            default:
                throw new NotImplementedException();
        }

        ctrl.CssClass = RemoveToken(ctrl.CssClass, "co3_invalid");

        if (!bParsed)
            ctrl.CssClass += " co3_invalid";

        return bParsed;
    }

    private static string RemoveToken(string value, string token)
    {
        string[] tokens = value.Split(' ');
        for (int i = 0; i < tokens.Length; ++i)
        {
            if (tokens[i] == token)
                Array.Clear(tokens, i, 1);
        }
        return string.Join(" ", tokens);
    }
}
