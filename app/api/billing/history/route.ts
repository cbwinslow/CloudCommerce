import { NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs';

// Get billing history
export async function GET() {
  try {
    const { userId } = auth();
    
    if (!userId) {
      return new NextResponse('Unauthorized', { status: 401 });
    }

    // In a real app, you would fetch this from your database
    // This is a simplified example
    const billingHistory = await prisma?.billingHistory.findMany({
      where: { userId },
      orderBy: { createdAt: 'desc' },
      take: 12, // Last 12 months
    });

    // Format the response
    const formattedHistory = (billingHistory || []).map((item) => ({
      id: item.id,
      date: item.createdAt.toISOString(),
      description: `Invoice #${item.stripeInvoiceId?.slice(-8) || 'N/A'}`,
      amount: Number(item.amount),
      status: item.status,
      invoiceUrl: item.metadata?.invoice_pdf,
    }));

    return NextResponse.json(formattedHistory);
  } catch (error) {
    console.error('Error fetching billing history:', error);
    return new NextResponse('Internal Server Error', { status: 500 });
  }
}
