<%@ Page Language="C#" AutoEventWireup="true" CodeFile="CreateIncident.aspx.cs" Inherits="CreateIncident" %>

<%@ Import Namespace="Co3.Rest.Dto" %>

<html xmlns="http://www.w3.org/1999/xhtml">
<head runat="server">
  <title></title>
  <link href="/styles/jquery-ui-timepicker-addon.css" rel="stylesheet" type="text/css" media="all" />
  <link href="/styles/styles.css" rel="stylesheet" type="text/css" media="all" />
  <link rel="stylesheet" href="//ajax.googleapis.com/ajax/libs/jqueryui/1.10.4/themes/smoothness/jquery-ui.css" />
  <script src="//ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.min.js"></script>
  <script src="//ajax.googleapis.com/ajax/libs/jqueryui/1.10.4/jquery-ui.min.js"></script>
  <script src="js/jquery-ui-timepicker-addon.js"></script>
</head>
<body>
  <div id="_co3_error_panel" runat="server" class="Notice" visible="false">
    <p>Service is temporarily unavailable.  Please try again later.</p>
    <div id="_co3_error_detail" runat="server" visible="false"></div>
  </div>
  <form id="IncidentForm" runat="server">
    <div class="Notice">
      This form demonstrates how to create an incident using ASP.net and the Resilient Systems REST API.<br />
      Please customize the page before deploying it!
    </div>
    <p>
      <label>Reporter (Your Name)</label>
      <asp:TextBox ID="co3_reporter" runat="server" />
    </p>
    <p>
      <label>Incident Type</label>
      <asp:CheckBoxList ID="co3_incident_type_ids" runat="server" RepeatLayout="UnorderedList" />
    </p>

    <p>
      <label>NIST Attack Vectors</label>
      <asp:CheckBoxList ID="co3_nist_attack_vectors" runat="server" RepeatLayout="UnorderedList" />
    </p>

    <p>
      <label>Incident Disposition</label>
      <asp:DropDownList ID="co3_confirmed" runat="server" />
    </p>
    <p>
      <label>Incident Description</label>
      <asp:TextBox ID="co3_description" runat="server" />
    </p>

    <p>
      <label>Incident name</label>
      <asp:TextBox ID="co3_name" runat="server" />
    </p>

    <p>
      <label>Date Discovery</label>
      <asp:TextBox ID="co3_discovered_date" runat="server" TextMode="DateTime" />
    </p>

    <p>
      <label>Address</label>
      <asp:TextBox ID="co3_addr" runat="server" />
    </p>

    <p>
      <label>City</label>
      <asp:TextBox ID="co3_city" runat="server" />
    </p>

    <p>
      <label>Country</label>
      <asp:DropDownList ID="co3_country" runat="server" />
    </p>

    <p>
      <label>State</label>
      <asp:DropDownList ID="co3_state" runat="server" />
    </p>

    <p>
      <label>Zip Code</label>
      <asp:TextBox ID="co3_zip" runat="server" />
    </p>

    <p>
      <label>Criminal or nefarious activity?</label>
      <asp:RadioButtonList ID="co3_crimestatus_id" runat="server" RepeatLayout="Flow" RepeatDirection="Horizontal" />
    </p>

    <p>
      <label>Jurisdiction</label>
      <asp:TextBox ID="co3_jurisdiction_name" runat="server" />
    </p>

    <p>
      <label>Exposure Type</label>
      <asp:DropDownList ID="co3_exposure_type_id" runat="server" />
    </p>

    <p>
      <label>Department</label>
      <asp:DropDownList ID="co3_exposure_dept_id" runat="server" />
    </p>

    <p>
      <label>Severity</label>
      <asp:DropDownList ID="co3_severity_code" runat="server" />
    </p>

    <p style="padding-left: 40em">
      <asp:Button ID="Co3Submit" runat="server" Text="Create Incident" />
    </p>
  </form>

  <script type="text/javascript">
    $("#<%=co3_discovered_date.ClientID %>").datetimepicker();
  </script>
</body>
</html>

<script runat="server">
  protected override void OnInit(EventArgs e)
  {
    base.OnInit(e);

    // add button click handler
    Co3Submit.Click += Co3Submit_Click;
  }
  void Co3Submit_Click(object sender, EventArgs e)
  {
    FullIncidentDataDto incident = new FullIncidentDataDto();
    
    // Uncomment the code below to add preset values such as reporter id 
    // and the reporter's ip address (custom field).  Note that you have to
    // create the corresponding custom field for custom data.  In this case,
    // the custom field is ip address.
    /*
    incident.Reporter = GetEmployeeId();
    incident.Properties.Add("ip", Request.UserHostAddress);
    */
    
    // if the incident was created, send the user to somewhere
    if (Co3CreateIncident(incident))
      Response.Redirect("http://www.resilientsystems.com");
  }

  // logic to display errors and exceptions to help with debugging
  protected override void OnHandleException(Exception ex, string message)
  {
    IncidentForm.Visible = false;
    _co3_error_panel.Visible = true;

    if (_co3_error_detail != null)
    {
      _co3_error_detail.Visible = true;
      _co3_error_detail.InnerText = ex.Message;

      if (!string.IsNullOrEmpty(message))
        _co3_error_detail.InnerText += " (" + message + ")";
    }
  }

</script>
